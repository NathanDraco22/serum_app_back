from fastapi import HTTPException, status
from repos.v1.cash_registers import (
    CashRegisterInDb,
    CashRegistersRepository,
    CreateCashRegister,
    UpdateCashRegister,
)
from repos.v1.cash_transactions import CashTransactionInDb
from core.cash_register.cash_register_manager import CashRegisterManager
from core.cash_register.process_opening import OpenCashIntent
from core.cash_register.process_closing import CloseCashIntent
from core.cash_register.process_income import IncomeIntent
from core.cash_register.process_withdrawal import WithdrawalIntent
from core.cash_register.process_payment import PaymentIntent
from core.exceptions import (
    CashRegisterAlreadyOpen,
    CashRegisterNotOpen,
    CashRegisterAlreadyClosed,
    ConceptRequired,
    InsufficientMethodBalance,
)

from responses.v1 import ListResponse
from .cash_registers_schemas import (
    OpenCashRegisterRequest,
    CloseCashRegisterRequest,
    IncomeRegisterRequest,
    WithdrawalRegisterRequest,
    PaymentRegisterRequest,
)


class CashRegistersController:
    def __init__(self, cash_registers_repo: CashRegistersRepository) -> None:
        self.cash_registers_repo = cash_registers_repo
        self.cash_register_manager = CashRegisterManager()

    async def create_cash_register(self, body: CreateCashRegister) -> CashRegisterInDb:
        return await self.cash_registers_repo.create_cash_register(body)

    async def get_all_cash_registers(self) -> ListResponse[CashRegisterInDb]:
        cash_registers = await self.cash_registers_repo.get_all_cash_registers()
        return ListResponse(count=len(cash_registers), data=cash_registers)

    async def get_cash_register_by_id(self, cash_register_id: str) -> CashRegisterInDb:
        cash_register = await self.cash_registers_repo.get_cash_register_by_id(
            cash_register_id
        )
        if cash_register is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash register not found",
            )
        return cash_register

    async def open_cash_register(
        self, cash_register_id: str, body: OpenCashRegisterRequest
    ) -> CashRegisterInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(
            cash_register_id
        )
        if register is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash register not found",
            )

        open_intent = OpenCashIntent(
            branchId=register.branchId,
            initialCash=body.initialCash,
            initialCard=body.initialCard,
            initialTransfer=body.initialTransfer,
            openedBy=body.openedBy,
        )

        try:
            return await self.cash_register_manager.open_register(
                register_id=cash_register_id, open_intent=open_intent
            )
        except CashRegisterAlreadyOpen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cash register is already open",
            )

    async def close_cash_register(
        self, cash_register_id: str, body: CloseCashRegisterRequest
    ) -> CashRegisterInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(
            cash_register_id
        )
        if register is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash register not found",
            )

        close_intent = CloseCashIntent(performedBy=body.performedBy)

        try:
            return await self.cash_register_manager.close_register(
                register_id=cash_register_id, close_intent=close_intent
            )
        except CashRegisterAlreadyClosed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cash register is already closed",
            )

    async def register_income(
        self, cash_register_id: str, body: IncomeRegisterRequest
    ) -> CashTransactionInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(
            cash_register_id
        )
        if register is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash register not found",
            )

        income_intent = IncomeIntent(
            amount=body.amount,
            paymentMethod=body.paymentMethod,
            concept=body.concept,
            performedBy=body.performedBy,
        )

        try:
            return await self.cash_register_manager.register_income(
                register_id=cash_register_id, income_intent=income_intent
            )
        except CashRegisterNotOpen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cash register is not open",
            )
        except ConceptRequired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Concept is required for income",
            )

    async def register_withdrawal(
        self, cash_register_id: str, body: WithdrawalRegisterRequest
    ) -> CashTransactionInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(
            cash_register_id
        )
        if register is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash register not found",
            )

        withdrawal_intent = WithdrawalIntent(
            amount=body.amount,
            paymentMethod=body.paymentMethod,
            concept=body.concept,
            performedBy=body.performedBy,
        )

        try:
            return await self.cash_register_manager.register_withdrawal(
                register_id=cash_register_id, withdrawal_intent=withdrawal_intent
            )
        except CashRegisterNotOpen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cash register is not open",
            )
        except ConceptRequired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Concept is required for withdrawal",
            )
        except InsufficientMethodBalance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance in the selected payment method",
            )

    async def register_payment(
        self, cash_register_id: str, body: PaymentRegisterRequest
    ) -> CashTransactionInDb:
        register = await self.cash_registers_repo.get_cash_register_by_id(
            cash_register_id
        )
        if register is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash register not found",
            )

        payment_intent = PaymentIntent(
            amount=body.amount,
            paymentMethod=body.paymentMethod,
            orderId=body.orderId,
            performedBy=body.performedBy,
        )

        try:
            return await self.cash_register_manager.register_payment(
                register_id=cash_register_id, payment_intent=payment_intent
            )
        except CashRegisterNotOpen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cash register is not open",
            )

    async def update_cash_register_by_id(
        self, cash_register_id: str, body: UpdateCashRegister
    ) -> CashRegisterInDb:
        updated_cash_register = (
            await self.cash_registers_repo.update_cash_register_by_id(
                cash_register_id, body
            )
        )
        if updated_cash_register is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash register not found",
            )
        return updated_cash_register

    async def delete_cash_register_by_id(
        self, cash_register_id: str
    ) -> CashRegisterInDb:
        deleted_cash_register = await (
            self.cash_registers_repo.delete_cash_register_by_id(cash_register_id)
        )
        if deleted_cash_register is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash register not found",
            )
        return deleted_cash_register


cash_registers_controller = CashRegistersController(
    cash_registers_repo=CashRegistersRepository.get_instance(),
)
