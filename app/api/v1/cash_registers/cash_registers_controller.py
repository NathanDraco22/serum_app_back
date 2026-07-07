from fastapi import HTTPException, status
from repos.v1.cash_registers import (
    CashRegisterInDb,
    CashRegistersRepository,
    CreateCashRegister,
    UpdateCashRegister,
)
from responses.v1 import ListResponse


class CashRegistersController:
    def __init__(self, cash_registers_repo: CashRegistersRepository) -> None:
        self.cash_registers_repo = cash_registers_repo

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
