from pydantic import BaseModel
from tools.uuid_tool import UuidTool
from tools.time_tools import TimeTools
from repos.v1.cash_transactions import CashTransactionInDb
from repos.v1.cash_registers import CashRegisterInDb, UpdateCashRegister
from repos.v1.common.models.user_info import UserInfo
from services import MongoService
from services.mongo_collections.v1 import (
    CashRegistersCollection,
    CashTransactionsCollection,
)
from core.exceptions import (
    CashRegisterNotFound,
    CashRegisterNotOpen,
    InvalidPaymentMethod,
)


class PaymentIntent(BaseModel):
    amount: int
    paymentMethod: str
    orderId: str
    performedBy: UserInfo


async def process_payment(
    register_id: str, payment_intent: PaymentIntent
) -> CashTransactionInDb:
    if payment_intent.paymentMethod not in ("cash", "card", "transfer"):
        raise InvalidPaymentMethod()

    mongo_client = MongoService().client
    register_col = CashRegistersCollection.get_instance()
    transaction_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind(end_session=False):
                register_data = await register_col.fetch_cash_register_by_id(
                    register_id
                )
                if register_data is None:
                    raise CashRegisterNotFound()

                register = CashRegisterInDb.model_validate(register_data)

                if not register.isOpen:
                    raise CashRegisterNotOpen()

                now = TimeTools.get_now_in_milliseconds()

                new_cash = register.cashBalance
                new_card = register.cardBalance
                new_transfer = register.transferBalance

                if payment_intent.paymentMethod == "cash":
                    new_cash += payment_intent.amount
                elif payment_intent.paymentMethod == "card":
                    new_card += payment_intent.amount
                elif payment_intent.paymentMethod == "transfer":
                    new_transfer += payment_intent.amount

                new_total = new_cash + new_card + new_transfer

                update_model = UpdateCashRegister(
                    cashBalance=new_cash,
                    cardBalance=new_card,
                    transferBalance=new_transfer,
                    totalBalance=new_total,
                )

                update_data = update_model.model_dump(exclude_unset=True)
                update_data["updatedAt"] = now

                await register_col.update_cash_register_by_id(
                    register_id, update_data
                )

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    registerId=register_id,
                    branchId=register.branchId,
                    flowType="in",
                    subType="payment",
                    paymentMethod=payment_intent.paymentMethod,
                    amount=payment_intent.amount,
                    resultingBalance=new_total,
                    concept="Pago de orden",
                    referenceId=payment_intent.orderId,
                    performedBy=payment_intent.performedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transaction_col.create_cash_transaction(transaction.model_dump())

                return transaction
