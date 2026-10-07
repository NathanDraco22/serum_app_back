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
    ConceptRequired,
    InsufficientMethodBalance,
    InvalidPaymentMethod,
)


class WithdrawalIntent(BaseModel):
    amount: int
    paymentMethod: str
    concept: str
    performedBy: UserInfo


async def process_withdrawal(
    register_id: str, withdrawal_intent: WithdrawalIntent
) -> CashTransactionInDb:
    if not withdrawal_intent.concept.strip():
        raise ConceptRequired()

    if withdrawal_intent.paymentMethod not in ("cash", "card", "transfer"):
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

                balance_to_check = getattr(
                    register, f"{withdrawal_intent.paymentMethod}Balance", 0
                )
                if withdrawal_intent.amount > balance_to_check:
                    raise InsufficientMethodBalance()

                now = TimeTools.get_now_in_milliseconds()

                new_cash = register.cashBalance
                new_card = register.cardBalance
                new_transfer = register.transferBalance

                if withdrawal_intent.paymentMethod == "cash":
                    new_cash -= withdrawal_intent.amount
                elif withdrawal_intent.paymentMethod == "card":
                    new_card -= withdrawal_intent.amount
                elif withdrawal_intent.paymentMethod == "transfer":
                    new_transfer -= withdrawal_intent.amount

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
                    flowType="out",
                    subType="withdrawal",
                    paymentMethod=withdrawal_intent.paymentMethod,
                    amount=withdrawal_intent.amount,
                    resultingBalance=new_total,
                    concept=withdrawal_intent.concept,
                    referenceId=None,
                    performedBy=withdrawal_intent.performedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transaction_col.create_cash_transaction(transaction.model_dump())

                return transaction
