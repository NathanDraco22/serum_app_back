from pydantic import BaseModel
from serum.tools.uuid_tool import UuidTool
from serum.tools.time_tools import TimeTools
from serum.repos.v1.cash_transactions import CashTransactionInDb
from serum.repos.v1.cash_registers import CashRegisterInDb, UpdateCashRegister
from serum.repos.v1.common.models.user_info import UserInfo
from serum.services import MongoService
from serum.services.mongo_collections.v1 import (
    CashRegistersCollection,
    CashTransactionsCollection,
)
from serum.core.exceptions import (
    CashRegisterNotFound,
    CashRegisterNotOpen,
    ConceptRequired,
    InvalidAmount,
    InvalidPaymentMethod,
)


class IncomeIntent(BaseModel):
    amount: int
    paymentMethod: str
    concept: str
    performedBy: UserInfo


async def process_income(
    register_id: str, income_intent: IncomeIntent
) -> CashTransactionInDb:
    if income_intent.amount <= 0:
        raise InvalidAmount()

    if not income_intent.concept.strip():
        raise ConceptRequired()

    if income_intent.paymentMethod not in ("cash", "card", "transfer"):
        raise InvalidPaymentMethod()

    mongo_client = MongoService().client
    register_col = CashRegistersCollection.get_instance()
    transaction_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind(end_session=False):
                register_data = await register_col.fetch_cash_register_by_id(
                    register_id, session=session
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

                if income_intent.paymentMethod == "cash":
                    new_cash += income_intent.amount
                elif income_intent.paymentMethod == "card":
                    new_card += income_intent.amount
                elif income_intent.paymentMethod == "transfer":
                    new_transfer += income_intent.amount

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
                    register_id, update_data, session=session
                )

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    registerId=register_id,
                    branchId=register.branchId,
                    flowType="in",
                    subType="income",
                    paymentMethod=income_intent.paymentMethod,
                    amount=income_intent.amount,
                    resultingBalance=new_total,
                    concept=income_intent.concept,
                    referenceId=None,
                    performedBy=income_intent.performedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transaction_col.create_cash_transaction(
                    transaction.model_dump(), session=session
                )

                return transaction
