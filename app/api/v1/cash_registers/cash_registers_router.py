from fastapi import APIRouter, Query
from serum.repos.v1.cash_registers import (
    CashRegisterInDb,
    CreateCashRegister,
    UpdateCashRegister,
)
from serum.repos.v1.cash_transactions import CashTransactionInDb
from responses.v1 import ListResponse

from .cash_registers_controller import cash_registers_controller
from .cash_registers_schemas import (
    OpenCashRegisterRequest,
    CloseCashRegisterRequest,
    IncomeRegisterRequest,
    WithdrawalRegisterRequest,
    PaymentRegisterRequest,
)

cash_registers_router = APIRouter(tags=["cashRegistersV1"])


@cash_registers_router.post("")
async def create_cash_register(body: CreateCashRegister) -> CashRegisterInDb:
    return await cash_registers_controller.create_cash_register(body)


@cash_registers_router.get("")
async def get_all_cash_registers(
    branch_id: str | None = Query(None),
) -> ListResponse[CashRegisterInDb]:
    return await cash_registers_controller.get_all_cash_registers(branch_id=branch_id)


@cash_registers_router.get("/{cash_register_id}")
async def get_cash_register_by_id(cash_register_id: str) -> CashRegisterInDb:
    return await cash_registers_controller.get_cash_register_by_id(cash_register_id)


@cash_registers_router.patch("/{cash_register_id}")
async def update_cash_register_by_id(
    cash_register_id: str, body: UpdateCashRegister
) -> CashRegisterInDb:
    return await cash_registers_controller.update_cash_register_by_id(
        cash_register_id, body
    )


@cash_registers_router.delete("/{cash_register_id}")
async def delete_cash_register_by_id(cash_register_id: str) -> CashRegisterInDb:
    return await cash_registers_controller.delete_cash_register_by_id(cash_register_id)


@cash_registers_router.post("/{cash_register_id}/open")
async def open_cash_register(
    cash_register_id: str, body: OpenCashRegisterRequest
) -> CashRegisterInDb:
    return await cash_registers_controller.open_cash_register(cash_register_id, body)


@cash_registers_router.post("/{cash_register_id}/close")
async def close_cash_register(
    cash_register_id: str, body: CloseCashRegisterRequest
) -> CashRegisterInDb:
    return await cash_registers_controller.close_cash_register(cash_register_id, body)


@cash_registers_router.post("/{cash_register_id}/income")
async def register_income(
    cash_register_id: str, body: IncomeRegisterRequest
) -> CashTransactionInDb:
    return await cash_registers_controller.register_income(cash_register_id, body)


@cash_registers_router.post("/{cash_register_id}/withdrawal")
async def register_withdrawal(
    cash_register_id: str, body: WithdrawalRegisterRequest
) -> CashTransactionInDb:
    return await cash_registers_controller.register_withdrawal(cash_register_id, body)


@cash_registers_router.post("/{cash_register_id}/payment")
async def register_payment(
    cash_register_id: str, body: PaymentRegisterRequest
) -> CashTransactionInDb:
    return await cash_registers_controller.register_payment(cash_register_id, body)
