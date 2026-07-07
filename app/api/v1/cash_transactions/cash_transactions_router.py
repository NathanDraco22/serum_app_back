from fastapi import APIRouter, Depends
from repos.v1.cash_transactions import CashTransactionInDb
from repos.v1.common.filter_params.cash_transaction_filter_params import (
    CashTransactionFilterParams,
)
from responses.v1 import ListResponse

from .cash_transactions_controller import cash_transactions_controller

cash_transactions_router = APIRouter(tags=["cashTransactionsV1"])


@cash_transactions_router.get("")
async def get_all_cash_transactions(
    query_params: CashTransactionFilterParams = Depends(),
) -> ListResponse[CashTransactionInDb]:
    return await cash_transactions_controller.get_all_cash_transactions(query_params)
