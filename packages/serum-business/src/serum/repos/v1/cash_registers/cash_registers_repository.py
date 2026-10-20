from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool

from .data.cash_registers_datasource import CashRegistersDataSource
from .models.cash_register_model import (
    CashRegisterInDb,
    CreateCashRegister,
    UpdateCashRegister,
)


class CashRegistersRepository:
    _instance: "CashRegistersRepository|None" = None

    def __init__(self, cash_registers_ds: CashRegistersDataSource):
        self.cash_registers_ds = cash_registers_ds

    @classmethod
    def get_instance(cls) -> "CashRegistersRepository":
        if cls._instance is None:
            cls._instance = cls(CashRegistersDataSource())
        return cls._instance

    async def create_cash_register(
        self, create_cash_register: CreateCashRegister
    ) -> CashRegisterInDb:
        new_cash_register = CashRegisterInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            **create_cash_register.model_dump(),
        )
        result = await self.cash_registers_ds.create_cash_register(
            new_cash_register.model_dump()
        )
        return CashRegisterInDb.model_validate(result)

    async def get_all_cash_registers(
        self, branch_id: str | None = None
    ) -> list[CashRegisterInDb]:
        results = await self.cash_registers_ds.get_all_cash_registers(branch_id=branch_id)
        return [CashRegisterInDb.model_validate(r) for r in results]

    async def get_cash_register_by_id(
        self, cash_register_id: str
    ) -> CashRegisterInDb | None:
        result = await self.cash_registers_ds.get_cash_register_by_id(cash_register_id)
        if result is None:
            return None
        return CashRegisterInDb.model_validate(result)

    async def get_open_register_by_branch(
        self, branch_id: str
    ) -> CashRegisterInDb | None:
        result = await self.cash_registers_ds.get_open_register_by_branch(branch_id)
        if result is None:
            return None
        return CashRegisterInDb.model_validate(result)

    async def update_cash_register_by_id(
        self, cash_register_id: str, cash_register: UpdateCashRegister
    ) -> CashRegisterInDb | None:
        updated_data = cash_register.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.cash_registers_ds.update_cash_register_by_id(
            cash_register_id, updated_data
        )
        if result is None:
            return None
        return CashRegisterInDb.model_validate(result)

    async def delete_cash_register_by_id(
        self, cash_register_id: str
    ) -> CashRegisterInDb | None:
        result = await self.cash_registers_ds.delete_cash_register_by_id(
            cash_register_id
        )
        if result is None:
            return None
        return CashRegisterInDb.model_validate(result)
