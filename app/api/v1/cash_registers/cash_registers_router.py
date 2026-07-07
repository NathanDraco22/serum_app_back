from fastapi import APIRouter
from repos.v1.cash_registers import (
    CashRegisterInDb,
    CreateCashRegister,
    UpdateCashRegister,
)
from responses.v1 import ListResponse

from .cash_registers_controller import cash_registers_controller

cash_registers_router = APIRouter(tags=["cashRegistersV1"])


@cash_registers_router.post("")
async def create_cash_register(body: CreateCashRegister) -> CashRegisterInDb:
    return await cash_registers_controller.create_cash_register(body)


@cash_registers_router.get("")
async def get_all_cash_registers() -> ListResponse[CashRegisterInDb]:
    return await cash_registers_controller.get_all_cash_registers()


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
