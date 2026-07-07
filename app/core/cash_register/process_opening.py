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


async def process_opening(
    branch_id: str,
    name: str,
    initial_cash: int,
    initial_card: int,
    initial_transfer: int,
    opened_by: UserInfo,
) -> CashRegisterInDb:
    mongo_client = MongoService().client
    register_col = CashRegistersCollection.get_instance()
    transaction_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind():
                total = initial_cash + initial_card + initial_transfer

                now = TimeTools.get_now_in_milliseconds()
                register_id = UuidTool.generate_uuid()

                register = CashRegisterInDb(
                    id=register_id,
                    branchId=branch_id,
                    name=name,
                    isOpen=True,
                    cashBalance=initial_cash,
                    cardBalance=initial_card,
                    transferBalance=initial_transfer,
                    totalBalance=total,
                    openedBy=opened_by,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await register_col.create_cash_register(register.model_dump())

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    registerId=register_id,
                    flowType="in",
                    subType="opening",
                    paymentMethod=None,
                    amount=total,
                    resultingBalance=total,
                    concept="Apertura de caja",
                    referenceId=None,
                    performedBy=opened_by,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transaction_col.create_cash_transaction(transaction.model_dump())

                return register
