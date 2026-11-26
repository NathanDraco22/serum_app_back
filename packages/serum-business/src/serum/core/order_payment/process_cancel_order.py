from collections import defaultdict

from serum.core.exceptions import (
    CashRegisterNotFound,
    CashRegisterNotOpen,
    CashShiftNotFound,
    CashShiftNotOpen,
    InsufficientMethodBalance,
    InvalidAmount,
    InvalidPaymentMethod,
    OrderCannotBeDeleted,
    OrderHasPayments,
    OrderNotFound,
)
from serum.repos.v1.cash_transactions import CashTransactionInDb
from serum.repos.v1.common.models.user_info import UserInfo
from serum.repos.v1.orders import OrderInDb, OrderStatusChange
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


async def process_cancel_order(
    order_id: str,
    reason: str,
    cancelled_by: UserInfo | None = None,
) -> OrderInDb:
    """Cancela una orden y revierte atómicamente sus recibos, saldos de caja y Kardex."""
    mongo_client = MongoService().client
    orders_col = OrdersCollection.get_instance()
    receipts_col = ReceiptsCollection.get_instance()
    shifts_col = CashShiftsCollection.get_instance()
    registers_col = CashRegistersCollection.get_instance()
    transactions_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind(end_session=False):
                # 1. Obtener y validar la orden
                order_data = await orders_col.fetch_order_by_id(
                    order_id, session=session
                )
                if order_data is None:
                    raise OrderNotFound()

                order = OrderInDb.model_validate(order_data)
                if order.status == "cancelled" or order.isDeleted:
                    raise OrderCannotBeDeleted()

                # 2. Obtener recibos activos asociados a la orden
                receipt_docs = await receipts_col.fetch_all_receipts(
                    {"orderId": order_id}, session=session
                )
                if order.paidAmount > 0 and not receipt_docs:
                    raise OrderHasPayments()

                receipts = [ReceiptInDb.model_validate(doc) for doc in receipt_docs]

                # 3. Pre-validación agrupada antes de mutar cualquier colección
                shift_totals: dict[str, dict[str, int]] = defaultdict(
                    lambda: defaultdict(int)
                )
                register_totals: dict[str, dict[str, int]] = defaultdict(
                    lambda: defaultdict(int)
                )

                for receipt in receipts:
                    if receipt.amount <= 0:
                        raise InvalidAmount()
                    if receipt.paymentMethod not in ("cash", "card", "transfer"):
                        raise InvalidPaymentMethod()
                    if receipt.shiftId:
                        shift_totals[receipt.shiftId][receipt.paymentMethod] += (
                            receipt.amount
                        )
                    elif receipt.registerId:
                        register_totals[receipt.registerId][receipt.paymentMethod] += (
                            receipt.amount
                        )
                    else:
                        raise CashShiftNotFound()

                for shift_id, methods_map in shift_totals.items():
                    shift_data = await shifts_col.fetch_cash_shift_by_id(
                        shift_id, session=session
                    )
                    if shift_data is None:
                        raise CashShiftNotFound()
                    if shift_data.get("status") != "OPEN":
                        raise CashShiftNotOpen()

                    for method, total_needed in methods_map.items():
                        if method == "cash":
                            available = shift_data.get(
                                "initialBalance", 0
                            ) + shift_data.get("cashBalance", 0)
                        else:
                            available = shift_data.get(f"{method}Balance", 0)
                        if total_needed > available:
                            raise InsufficientMethodBalance()

                for register_id, methods_map in register_totals.items():
                    reg_data = await registers_col.fetch_cash_register_by_id(
                        register_id, session=session
                    )
                    if reg_data is None:
                        raise CashRegisterNotFound()
                    if not reg_data.get("isOpen", False):
                        raise CashRegisterNotOpen()

                    for method, total_needed in methods_map.items():
                        available = reg_data.get(f"{method}Balance", 0)
                        if total_needed > available:
                            raise InsufficientMethodBalance()

                # 4. Revertir saldos, anular recibos y registrar contra-asientos en Kardex
                now = TimeTools.get_now_in_milliseconds()
                for receipt in receipts:
                    if receipt.shiftId:
                        updated_shift = await shifts_col.add_to_balance(
                            receipt.shiftId,
                            receipt.paymentMethod,
                            -receipt.amount,
                            session=session,
                        )
                        if updated_shift is None:
                            raise InsufficientMethodBalance()
                        resulting_balance = updated_shift.get("totalBalance", 0)
                    else:
                        updated_reg = await registers_col.subtract_from_balance(
                            receipt.registerId or "",
                            receipt.paymentMethod,
                            receipt.amount,
                            session=session,
                        )
                        if updated_reg is None:
                            raise CashRegisterNotOpen()
                        resulting_balance = updated_reg.get("totalBalance", 0)

                    await receipts_col.delete_receipt_by_id(
                        receipt.id, session=session, now=now
                    )

                    receipt_label = receipt.receiptNumber or receipt.id
                    transaction = CashTransactionInDb(
                        id=UuidTool.generate_uuid(),
                        shiftId=receipt.shiftId,
                        registerId=receipt.registerId,
                        branchId=receipt.branchId,
                        flowType="out",
                        subType="payment_reversal",
                        paymentMethod=receipt.paymentMethod,
                        amount=receipt.amount,
                        resultingBalance=resulting_balance,
                        concept=(
                            f"[Anulación de orden #{order.id}] "
                            f"Reversión de recibo #{receipt_label} — Motivo: {reason}"
                        ),
                        referenceId=order.id,
                        performedBy=cancelled_by or receipt.performedBy,
                        createdAt=now,
                        updatedAt=None,
                        isDeleted=False,
                    )
                    await transactions_col.create_cash_transaction(
                        transaction.model_dump(), session=session
                    )

                # 5. Cancelar la orden y limpiar monto pagado
                history = [entry.model_dump() for entry in order.statusHistory]
                history.append(
                    OrderStatusChange(
                        status="cancelled",
                        changedAt=now,
                        changedBy=cancelled_by,
                        reason=reason,
                    ).model_dump()
                )
                cancellation_data: dict = {
                    "status": "cancelled",
                    "isDeleted": True,
                    "paidAmount": 0,
                    "updatedAt": now,
                    "cancelledAt": now,
                    "cancellationReason": reason,
                    "statusHistory": history,
                }
                if cancelled_by is not None:
                    cancellation_data["cancelledBy"] = cancelled_by.model_dump()

                cancelled_doc = await orders_col.cancel_order_by_id(
                    order_id, cancellation_data, session=session
                )
                if cancelled_doc is None:
                    raise OrderNotFound()

                return OrderInDb.model_validate(cancelled_doc)
