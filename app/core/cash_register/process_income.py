from tools.uuid_tool import UuidTool
from tools.time_tools import TimeTools
from repos.v1.cash_transactions import CashTransactionInDb
from repos.v1.cash_registers import CashRegisterInDb
from repos.v1.common.models.user_info import UserInfo
from services import MongoService
from services.mongo_collections.v1 import (
    CashRegistersCollection,
    CashTransactionsCollection,
)


async def process_income(
    register_id: str,
    amount: int,
    payment_method: str,
    concept: str,
    performed_by: UserInfo,
) -> CashTransactionInDb:
    if not concept.strip():
        raise ValueError("CONCEPT_REQUIRED_FOR_INCOME")

    mongo_client = MongoService().client
    register_col = CashRegistersCollection.get_instance()
    transaction_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind():
                register_data = await register_col.fetch_cash_register_by_id(
                    register_id
                )
                if register_data is None:
                    raise ValueError("REGISTER_NOT_FOUND")

                register = CashRegisterInDb.model_validate(register_data)

                if not register.isOpen:
                    raise ValueError("REGISTER_NOT_OPEN")

                now = TimeTools.get_now_in_milliseconds()

                new_cash = register.cashBalance
                new_card = register.cardBalance
                new_transfer = register.transferBalance

                if payment_method == "cash":
                    new_cash += amount
                elif payment_method == "card":
                    new_card += amount
                elif payment_method == "transfer":
                    new_transfer += amount

                new_total = new_cash + new_card + new_transfer

                await register_col.update_cash_register_by_id(
                    register_id,
                    {
                        "updatedAt": now,
                        "cashBalance": new_cash,
                        "cardBalance": new_card,
                        "transferBalance": new_transfer,
                        "totalBalance": new_total,
                    },
                )

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    registerId=register_id,
                    flowType="in",
                    subType="income",
                    paymentMethod=payment_method,
                    amount=amount,
                    resultingBalance=new_total,
                    concept=concept,
                    referenceId=None,
                    performedBy=performed_by,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transaction_col.create_cash_transaction(transaction.model_dump())

                return transaction
