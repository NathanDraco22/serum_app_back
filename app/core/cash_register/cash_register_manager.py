import asyncio

from pymongo.errors import OperationFailure
from repos.v1.cash_registers import (
    CashRegisterInDb,
    CashRegistersDataSource,
    CashRegistersRepository,
)
from repos.v1.cash_transactions import CashTransactionInDb
from core.exceptions import (
    CashRegisterAlreadyOpen,
    CashRegisterNotFound,
    CashRegisterNotOpen,
    CashRegisterAlreadyClosed,
    ConceptRequired,
    InsufficientMethodBalance,
)

from .process_closing import process_closing, CloseCashIntent
from .process_income import process_income, IncomeIntent
from .process_opening import process_opening, OpenCashIntent
from .process_payment import process_payment, PaymentIntent
from .process_withdrawal import process_withdrawal, WithdrawalIntent


class CashRegisterManager:
    def __init__(self) -> None:
        self.cash_registers_repo = CashRegistersRepository(
            cash_registers_ds=CashRegistersDataSource()
        )

    async def open_register(
        self, register_id: str, open_intent: OpenCashIntent
    ) -> CashRegisterInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(register_id)
        if register is None:
            raise CashRegisterNotFound()
        if register.isOpen:
            raise CashRegisterAlreadyOpen()

        existing = await self.cash_registers_repo.get_open_register_by_branch(
            open_intent.branchId
        )
        if existing is not None:
            raise CashRegisterAlreadyOpen()

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_opening(
                    register_id=register_id, open_intent=open_intent
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise

        raise RuntimeError("Server is too busy, try again later")

    async def close_register(
        self, register_id: str, close_intent: CloseCashIntent
    ) -> CashRegisterInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(register_id)
        if register is None:
            raise CashRegisterNotFound()
        if not register.isOpen:
            raise CashRegisterAlreadyClosed()

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_closing(
                    register_id=register_id, close_intent=close_intent
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise

        raise RuntimeError("Server is too busy, try again later")

    async def register_income(
        self, register_id: str, income_intent: IncomeIntent
    ) -> CashTransactionInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(register_id)
        if register is None:
            raise CashRegisterNotFound()
        if not register.isOpen:
            raise CashRegisterNotOpen()
        if not income_intent.concept.strip():
            raise ConceptRequired()

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_income(
                    register_id=register_id, income_intent=income_intent
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise

        raise RuntimeError("Server is too busy, try again later")

    async def register_withdrawal(
        self, register_id: str, withdrawal_intent: WithdrawalIntent
    ) -> CashTransactionInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(register_id)
        if register is None:
            raise CashRegisterNotFound()
        if not register.isOpen:
            raise CashRegisterNotOpen()
        if not withdrawal_intent.concept.strip():
            raise ConceptRequired()

        balance_to_check = getattr(
            register, f"{withdrawal_intent.paymentMethod}Balance", 0
        )
        if withdrawal_intent.amount > balance_to_check:
            raise InsufficientMethodBalance()

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_withdrawal(
                    register_id=register_id, withdrawal_intent=withdrawal_intent
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise

        raise RuntimeError("Server is too busy, try again later")

    async def register_payment(
        self, register_id: str, payment_intent: PaymentIntent
    ) -> CashTransactionInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(register_id)
        if register is None:
            raise CashRegisterNotFound()
        if not register.isOpen:
            raise CashRegisterNotOpen()

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_payment(
                    register_id=register_id, payment_intent=payment_intent
                )
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise

        raise RuntimeError("Server is too busy, try again later")
