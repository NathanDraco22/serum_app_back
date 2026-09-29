from tools.uuid_tool import UuidTool
from tools.time_tools import TimeTools
from repos.v1.orders import OrderInDb, UpdateOrder
from repos.v1.cash_transactions import CashTransactionInDb
from services import MongoService
from services.mongo_collections.v1 import (
    OrdersCollection,
    CashRegistersCollection,
    CashTransactionsCollection,
)
from core.exceptions import (
    CashRegisterNotFound,
    CashRegisterNotOpen,
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
    transactions_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind():
                register_data = await registers_col.fetch_cash_register_by_id(
                    pay_intent.registerId
                )
                if register_data is None:
                    raise CashRegisterNotFound()
                if not register_data.get("isOpen", False):
                    raise CashRegisterNotOpen()

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
                if order.status == "completed":
                    new_status = "completed"
                else:
                    new_status = (
                        "paid"
                        if new_paid_amount >= order.totalPrice
                        else "partiallyPaid"
                    )

                update_model = UpdateOrder(
                    status=new_status,
                    paidAmount=new_paid_amount,
                )
                update_data = update_model.model_dump(exclude_unset=True)
                update_data["updatedAt"] = now

                updated_order_data = await orders_col.update_order_by_id(
                    pay_intent.orderId, update_data
                )

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

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    registerId=pay_intent.registerId,
                    branchId=register_data.get("branchId", ""),
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
