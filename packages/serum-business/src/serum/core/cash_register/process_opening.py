from pydantic import BaseModel
from serum.tools.uuid_tool import UuidTool
from serum.tools.time_tools import TimeTools
from serum.repos.v1.cash_registers import CashRegisterInDb, UpdateCashRegister
from serum.repos.v1.cash_transactions import CashTransactionInDb
from serum.repos.v1.common.models.user_info import UserInfo
from serum.services import MongoService
from serum.services.mongo_collections.v1 import (
    CashRegistersCollection,
    CashTransactionsCollection,
)
from serum.core.exceptions import CashRegisterNotFound, CashRegisterAlreadyOpen


class OpenCashIntent(BaseModel):
    branchId: str
    initialCash: int
    initialCard: int
    initialTransfer: int
    openedBy: UserInfo


async def process_opening(
    register_id: str, open_intent: OpenCashIntent
) -> CashRegisterInDb:
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

                if register_data.get("isOpen", False):
                    raise CashRegisterAlreadyOpen()

                existing = await register_col.fetch_open_register_by_branch(
                    open_intent.branchId
                )
                if existing is not None:
                    raise CashRegisterAlreadyOpen()

                now = TimeTools.get_now_in_milliseconds()

                total = (
                    open_intent.initialCash
                    + open_intent.initialCard
                    + open_intent.initialTransfer
                )

                update_model = UpdateCashRegister(
                    isOpen=True,
                    cashBalance=open_intent.initialCash,
                    cardBalance=open_intent.initialCard,
                    transferBalance=open_intent.initialTransfer,
                    totalBalance=total,
                    openedBy=open_intent.openedBy,
                )

                update_data = update_model.model_dump(
                    exclude_unset=True, exclude_none=True
                )
                update_data["updatedAt"] = now

                updated = await register_col.update_cash_register_by_id(
                    register_id, update_data
                )

                register = CashRegisterInDb.model_validate(updated)

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    registerId=register_id,
                    branchId=register.branchId,
                    flowType="in",
                    subType="opening",
                    paymentMethod=None,
                    amount=total,
                    resultingBalance=total,
                    concept="Apertura de caja",
                    referenceId=None,
                    performedBy=open_intent.openedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transaction_col.create_cash_transaction(transaction.model_dump())

                return register
