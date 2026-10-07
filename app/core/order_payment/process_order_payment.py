from tools.uuid_tool import UuidTool
from tools.time_tools import TimeTools
from repos.v1.orders import OrderInDb, UpdateOrder
from repos.v1.cash_transactions import CashTransactionInDb
from services import MongoService
from services.mongo_collections.v1 import (
    OrdersCollection,
    CashRegistersCollection,
    CashShiftsCollection,
    CashTransactionsCollection,
)
from core.exceptions import (
    CashRegisterNotFound,
    CashRegisterNotOpen,
    CashShiftNotFound,
    CashShiftNotOpen,
    InvalidPaymentMethod,
    OrderNotFound,
    OrderAlreadyPaid,
)

from .order_payment import OrderPayIntent


async def process_order_payment(pay_intent: OrderPayIntent) -> OrderInDb:
    if pay_intent.paymentMethod not in ("cash", "card", "transfer"):
        raise InvalidPaymentMethod()

    mongo_client = MongoService().client
    orders_col = OrdersCollection.get_instance()
    registers_col = CashRegistersCollection.get_instance()
    shifts_col = CashShiftsCollection.get_instance()
    transactions_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind(end_session=False):
                branch_id = ""
                resulting_balance = 0

                if pay_intent.shiftId:
                    shift_data = await shifts_col.fetch_cash_shift_by_id(
                        pay_intent.shiftId
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
                    )
                    resulting_balance = (
                        updated_shift.get("totalBalance", 0)
                        if updated_shift
                        else 0
                    )
                elif pay_intent.registerId:
                    register_data = await registers_col.fetch_cash_register_by_id(
                        pay_intent.registerId
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
                    )
                    resulting_balance = (
                        updated_register.get("totalBalance", 0)
                        if updated_register
                        else 0
                    )
                else:
                    raise CashShiftNotFound()

                order_data = await orders_col.fetch_order_by_id(
                    pay_intent.orderId
                )
                if order_data is None:
                    raise OrderNotFound()

                order = OrderInDb.model_validate(order_data)

                if order.status not in ("pending", "partiallyPaid", "completed") or (
                    order.totalPrice > 0 and order.paidAmount >= order.totalPrice
                ):
                    raise OrderAlreadyPaid()

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
                    pay_intent.orderId, update_data
                )

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
                    concept="Pago de orden",
                    referenceId=pay_intent.orderId,
                    performedBy=pay_intent.performedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transactions_col.create_cash_transaction(
                    transaction.model_dump()
                )

                return OrderInDb.model_validate(updated_order_data)
