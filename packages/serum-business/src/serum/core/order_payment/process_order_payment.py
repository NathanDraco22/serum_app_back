from serum.core.counter_manager import CounterManager
from serum.core.exceptions import (
    CashRegisterNotFound,
    CashRegisterNotOpen,
    CashShiftNotFound,
    CashShiftNotOpen,
    InvalidAmount,
    InvalidPaymentMethod,
    OrderAlreadyPaid,
    OrderNotFound,
)
from serum.repos.v1.cash_transactions import CashTransactionInDb
from serum.repos.v1.orders import OrderInDb, UpdateOrder
from serum.repos.v1.receipts import ReceiptInDb
from serum.services import MongoService
from serum.services.mongo_collections.v1 import (
    CashRegistersCollection,
    CashShiftsCollection,
    CashTransactionsCollection,
    OrdersCollection,
    ReceiptsCollection,
)
from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool

from .order_payment import OrderPayIntent



async def process_order_payment(pay_intent: OrderPayIntent) -> OrderInDb:
    if pay_intent.amount <= 0:
        raise InvalidAmount()

    if pay_intent.paymentMethod not in ("cash", "card", "transfer"):
        raise InvalidPaymentMethod()

    mongo_client = MongoService().client
    orders_col = OrdersCollection.get_instance()
    registers_col = CashRegistersCollection.get_instance()
    shifts_col = CashShiftsCollection.get_instance()
    transactions_col = CashTransactionsCollection.get_instance()
    receipts_col = ReceiptsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind(end_session=False):
                # 1. Validar la orden primero antes de mutar saldos
                order_data = await orders_col.fetch_order_by_id(
                    pay_intent.orderId, session=session
                )
                if order_data is None:
                    raise OrderNotFound()

                order = OrderInDb.model_validate(order_data)

                if (
                    order.status == "cancelled"
                    or order.totalPrice <= 0
                    or order.paidAmount >= order.totalPrice
                ):
                    raise OrderAlreadyPaid()

                pending_amount = order.totalPrice - order.paidAmount
                if pay_intent.amount > pending_amount:
                    raise InvalidAmount()

                # 2. Validar y actualizar el turno de caja o la caja registradora
                branch_id = ""
                resulting_balance = 0

                if pay_intent.shiftId:
                    shift_data = await shifts_col.fetch_cash_shift_by_id(
                        pay_intent.shiftId, session=session
                    )
                    if shift_data is None:
                        raise CashShiftNotFound()
                    if shift_data.get("status") != "OPEN":
                        raise CashShiftNotOpen()
                    branch_id = shift_data.get("branchId", "")

                    updated_shift = await shifts_col.add_to_balance(
                        pay_intent.shiftId,
                        pay_intent.paymentMethod,
                        pay_intent.amount,
                        session=session,
                    )
                    resulting_balance = (
                        updated_shift.get("totalBalance", 0)
                        if updated_shift
                        else 0
                    )
                elif pay_intent.registerId:
                    register_data = await registers_col.fetch_cash_register_by_id(
                        pay_intent.registerId, session=session
                    )
                    if register_data is None:
                        raise CashRegisterNotFound()
                    if not register_data.get("isOpen", False):
                        raise CashRegisterNotOpen()
                    branch_id = register_data.get("branchId", "")

                    updated_register = await registers_col.add_to_balance(
                        pay_intent.registerId,
                        pay_intent.paymentMethod,
                        pay_intent.amount,
                        session=session,
                    )
                    resulting_balance = (
                        updated_register.get("totalBalance", 0)
                        if updated_register
                        else 0
                    )
                else:
                    raise CashShiftNotFound()

                # 3. Actualizar la orden
                now = TimeTools.get_now_in_milliseconds()
                new_paid_amount = order.paidAmount + pay_intent.amount
                has_all_results = len(order.results) > 0 and all(
                    r.resultValue is not None and str(r.resultValue).strip() != ""
                    for r in order.results
                )

                if new_paid_amount >= order.totalPrice:
                    new_status = "completed" if has_all_results else "paid"
                else:
                    new_status = "partiallyPaid"

                update_model = UpdateOrder(
                    status=new_status,
                    paidAmount=new_paid_amount,
                )
                update_data = update_model.model_dump(exclude_unset=True)
                update_data["updatedAt"] = now

                updated_order_data = await orders_col.update_order_by_id(
                    pay_intent.orderId, update_data, session=session
                )

                # 4. Crear Recibo secuencial atómico
                receipt_number = await CounterManager().next_receipt_number(
                    session=session
                )
                patient_name = (
                    order.patientInfo.name if order.patientInfo else None
                )
                receipt_concept = (
                    f"Abono a orden #{order.id}"
                    if new_status == "partiallyPaid"
                    else f"Liquidación de orden #{order.id}"
                )

                receipt = ReceiptInDb(
                    id=receipt_number,
                    receiptNumber=receipt_number,
                    orderId=order.id,
                    orderNumber=order.id,
                    branchId=branch_id,
                    shiftId=pay_intent.shiftId,
                    registerId=pay_intent.registerId,
                    amount=pay_intent.amount,
                    paymentMethod=pay_intent.paymentMethod,
                    concept=receipt_concept,
                    performedBy=pay_intent.performedBy,
                    patientName=patient_name,
                    referenceNumber=pay_intent.referenceNumber,
                    bank=pay_intent.bank,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )
                await receipts_col.create_receipt(
                    receipt.model_dump(), session=session
                )

                # 5. Registrar Transacción en Kardex
                tx_concept = f"Pago de orden #{order.id} (Recibo #{receipt_number})"
                if pay_intent.paymentMethod == "transfer":
                    transfer_details = []
                    if pay_intent.bank:
                        transfer_details.append(f"Banco: {pay_intent.bank}")
                    if pay_intent.referenceNumber:
                        transfer_details.append(f"Ref: {pay_intent.referenceNumber}")
                    if transfer_details:
                        tx_concept += f" [{' - '.join(transfer_details)}]"

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    shiftId=pay_intent.shiftId,
                    registerId=pay_intent.registerId,
                    branchId=branch_id,
                    flowType="in",
                    subType="payment",
                    paymentMethod=pay_intent.paymentMethod,
                    amount=pay_intent.amount,
                    resultingBalance=resulting_balance,
                    concept=tx_concept,
                    referenceId=pay_intent.orderId,
                    performedBy=pay_intent.performedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transactions_col.create_cash_transaction(
                    transaction.model_dump(), session=session
                )

                return OrderInDb.model_validate(updated_order_data)
