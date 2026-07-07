from tools.uuid_tool import UuidTool
from tools.time_tools import TimeTools
from repos.v1.cash_registers import CashRegisterInDb
from repos.v1.cash_transactions import CashTransactionInDb
from repos.v1.common.models.user_info import UserInfo
from services import MongoService
from services.mongo_collections.v1 import (
    CashRegistersCollection,
    CashTransactionsCollection,
)


async def process_closing(
    register_id: str,
    performed_by: UserInfo,
) -> CashRegisterInDb:
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
                    raise ValueError("REGISTER_ALREADY_CLOSED")

                now = TimeTools.get_now_in_milliseconds()

                closing_amount = register.totalBalance

                new_total = 0

                updated_data = await register_col.update_cash_register_by_id(
                    register_id,
                    {
                        "updatedAt": now,
                        "isOpen": False,
                        "cashBalance": 0,
                        "cardBalance": 0,
                        "transferBalance": 0,
                        "totalBalance": new_total,
                    },
                )

                updated_register = CashRegisterInDb.model_validate(updated_data)

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    registerId=register_id,
                    flowType="out",
                    subType="closing",
                    paymentMethod=None,
                    amount=closing_amount,
                    resultingBalance=new_total,
                    concept="Cierre de caja",
                    referenceId=None,
                    performedBy=performed_by,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transaction_col.create_cash_transaction(transaction.model_dump())

                return updated_register
