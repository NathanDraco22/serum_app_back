import asyncio

from pymongo.errors import OperationFailure
from repos.v1.cash_registers import (
    CashRegisterInDb,
    CashRegistersDataSource,
    CashRegistersRepository,
)
from repos.v1.cash_transactions import (
    CashTransactionInDb,
    CashTransactionsDataSource,
    CashTransactionsRepository,
)
from repos.v1.common.models.user_info import UserInfo

from .process_closing import process_closing
from .process_income import process_income
from .process_opening import process_opening
from .process_payment import process_payment
from .process_withdrawal import process_withdrawal


class CashRegisterManager:
    def __init__(self) -> None:
        self.cash_registers_repo = CashRegistersRepository(
            cash_registers_ds=CashRegistersDataSource()
        )
        self.cash_transactions_repo = CashTransactionsRepository(
            cash_transactions_ds=CashTransactionsDataSource()
        )

    async def open_register(
        self,
        branch_id: str,
        name: str,
        initial_cash: int,
        initial_card: int,
        initial_transfer: int,
        opened_by: UserInfo,
    ) -> CashRegisterInDb:
        existing = await self.cash_registers_repo.get_open_register_by_branch(branch_id)
        if existing is not None:
            raise ValueError("BRANCH_ALREADY_HAS_OPEN_REGISTER")

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_opening(
                    branch_id=branch_id,
                    name=name,
                    initial_cash=initial_cash,
                    initial_card=initial_card,
                    initial_transfer=initial_transfer,
                    opened_by=opened_by,
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise
            except Exception:
                raise

        raise RuntimeError("Server is too busy, try again later")

    async def close_register(
        self, register_id: str, performed_by: UserInfo
    ) -> CashRegisterInDb:
        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_closing(
                    register_id=register_id,
                    performed_by=performed_by,
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise
            except Exception:
                raise

        raise RuntimeError("Server is too busy, try again later")

    async def register_income(
        self,
        register_id: str,
        amount: int,
        payment_method: str,
        concept: str,
        performed_by: UserInfo,
    ) -> CashTransactionInDb:
        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_income(
                    register_id=register_id,
                    amount=amount,
                    payment_method=payment_method,
                    concept=concept,
                    performed_by=performed_by,
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise
            except Exception:
                raise

        raise RuntimeError("Server is too busy, try again later")

    async def register_withdrawal(
        self,
        register_id: str,
        amount: int,
        payment_method: str,
        concept: str,
        performed_by: UserInfo,
    ) -> CashTransactionInDb:
        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_withdrawal(
                    register_id=register_id,
                    amount=amount,
                    payment_method=payment_method,
                    concept=concept,
                    performed_by=performed_by,
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise
            except Exception:
                raise

        raise RuntimeError("Server is too busy, try again later")

    async def register_payment(
        self,
        register_id: str,
        amount: int,
        payment_method: str,
        order_id: str,
        performed_by: UserInfo,
    ) -> CashTransactionInDb:
        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_payment(
                    register_id=register_id,
                    amount=amount,
                    payment_method=payment_method,
                    order_id=order_id,
                    performed_by=performed_by,
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise
            except Exception:
                raise

        raise RuntimeError("Server is too busy, try again later")
