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
from serum.core.exceptions import CashRegisterNotFound, CashRegisterAlreadyClosed


class CloseCashIntent(BaseModel):
    performedBy: UserInfo


async def process_closing(
    register_id: str, close_intent: CloseCashIntent
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

                register = CashRegisterInDb.model_validate(register_data)

                if not register.isOpen:
                    raise CashRegisterAlreadyClosed()

                now = TimeTools.get_now_in_milliseconds()

                closing_amount = register.totalBalance

                update_model = UpdateCashRegister(
                    isOpen=False,
                    cashBalance=0,
                    cardBalance=0,
                    transferBalance=0,
                    totalBalance=0,
                )

                update_data = update_model.model_dump(exclude_unset=True)
                update_data["updatedAt"] = now

                updated_data = await register_col.update_cash_register_by_id(
                    register_id, update_data
                )

                updated_register = CashRegisterInDb.model_validate(updated_data)

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    registerId=register_id,
                    branchId=register.branchId,
                    flowType="out",
                    subType="closing",
                    paymentMethod=None,
                    amount=closing_amount,
                    resultingBalance=0,
                    concept="Cierre de caja",
                    referenceId=None,
                    performedBy=close_intent.performedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transaction_col.create_cash_transaction(transaction.model_dump())

                return updated_register
