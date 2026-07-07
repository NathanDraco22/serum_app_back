from repos.v1.cash_transactions import (
    CashTransactionInDb,
    CashTransactionsDataSource,
    CashTransactionsRepository,
)
from repos.v1.common.filter_params.cash_transaction_filter_params import (
    CashTransactionFilterParams,
)
from responses.v1 import ListResponse


class CashTransactionsController:
    def __init__(
        self,
        cash_transactions_repo: CashTransactionsRepository,
    ) -> None:
        self.cash_transactions_repo = cash_transactions_repo

    async def get_all_cash_transactions(
        self, query_params: CashTransactionFilterParams
    ) -> ListResponse[CashTransactionInDb]:
        transactions = await self.cash_transactions_repo.get_all_cash_transactions(
            query_params
        )
        return ListResponse(count=len(transactions), data=transactions)


cash_transactions_controller = CashTransactionsController(
    cash_transactions_repo=CashTransactionsRepository(
        cash_transactions_ds=CashTransactionsDataSource()
    )
)
