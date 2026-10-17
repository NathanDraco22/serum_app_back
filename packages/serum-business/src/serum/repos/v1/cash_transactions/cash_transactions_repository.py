from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool
from serum.repos.v1.common.filter_params.cash_transaction_filter_params import (
    CashTransactionFilterParams,
)

from .data.cash_transactions_datasource import CashTransactionsDataSource
from .models.cash_transaction_model import (
    CashTransactionInDb,
    CreateCashTransaction,
    UpdateCashTransaction,
)


class CashTransactionsRepository:
    _instance: "CashTransactionsRepository|None" = None

    def __init__(self, cash_transactions_ds: CashTransactionsDataSource):
        self.cash_transactions_ds = cash_transactions_ds

    @classmethod
    def get_instance(cls) -> "CashTransactionsRepository":
        if cls._instance is None:
            cls._instance = cls(CashTransactionsDataSource())
        return cls._instance

    async def create_cash_transaction(
        self, create_cash_transaction: CreateCashTransaction
    ) -> CashTransactionInDb:
        new_cash_transaction = CashTransactionInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            **create_cash_transaction.model_dump(),
        )
        result = await self.cash_transactions_ds.create_cash_transaction(
            new_cash_transaction.model_dump()
        )
        return CashTransactionInDb.model_validate(result)

    async def get_all_cash_transactions(
        self, filters: CashTransactionFilterParams | None = None
    ) -> list[CashTransactionInDb]:
        filters_dict = None
        if filters is not None:
            filters_dict = filters.model_dump(exclude_none=True)
        results = await self.cash_transactions_ds.get_all_cash_transactions(
            filters_dict
        )
        return [CashTransactionInDb.model_validate(r) for r in results]

    async def get_cash_transaction_by_id(
        self, cash_transaction_id: str
    ) -> CashTransactionInDb | None:
        result = await self.cash_transactions_ds.get_cash_transaction_by_id(
            cash_transaction_id
        )
        if result is None:
            return None
        return CashTransactionInDb.model_validate(result)

    async def update_cash_transaction_by_id(
        self, cash_transaction_id: str, cash_transaction: UpdateCashTransaction
    ) -> CashTransactionInDb | None:
        updated_data = cash_transaction.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.cash_transactions_ds.update_cash_transaction_by_id(
            cash_transaction_id, updated_data
        )
        if result is None:
            return None
        return CashTransactionInDb.model_validate(result)

    async def delete_cash_transaction_by_id(
        self, cash_transaction_id: str
    ) -> CashTransactionInDb | None:
        result = await self.cash_transactions_ds.delete_cash_transaction_by_id(
            cash_transaction_id
        )
        if result is None:
            return None
        return CashTransactionInDb.model_validate(result)
