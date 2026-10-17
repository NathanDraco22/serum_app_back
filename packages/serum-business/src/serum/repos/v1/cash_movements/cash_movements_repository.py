from serum.repos.v1.common.filter_params import CashMovementFilterParams
from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool

from .data.cash_movements_datasource import CashMovementsDataSource
from .models.cash_movement_model import (
    CashMovementInDb,
    CreateCashMovement,
    UpdateCashMovement,
)


class CashMovementsRepository:
    _instance: "CashMovementsRepository|None" = None

    def __init__(self, cash_movements_ds: CashMovementsDataSource):
        self.cash_movements_ds = cash_movements_ds

    @classmethod
    def get_instance(cls) -> "CashMovementsRepository":
        if cls._instance is None:
            cls._instance = cls(CashMovementsDataSource())
        return cls._instance

    async def create_cash_movement(
        self, create_cash_movement: CreateCashMovement
    ) -> CashMovementInDb:
        now = TimeTools.get_now_in_milliseconds()
        new_movement = CashMovementInDb(
            id=UuidTool.generate_uuid(),
            createdAt=now,
            updatedAt=None,
            isDeleted=False,
            **create_cash_movement.model_dump(),
        )
        result = await self.cash_movements_ds.create_cash_movement(
            new_movement.model_dump()
        )
        return CashMovementInDb.model_validate(result)

    async def get_all_cash_movements(
        self, filters: CashMovementFilterParams | None = None
    ) -> list[CashMovementInDb]:
        filters_dict = None
        if filters is not None:
            filters_dict = filters.model_dump(exclude_none=True)
        results = await self.cash_movements_ds.get_all_cash_movements(
            filters_dict
        )
        return [CashMovementInDb.model_validate(result) for result in results]

    async def get_cash_movement_by_id(
        self, cash_movement_id: str
    ) -> CashMovementInDb | None:
        result = await self.cash_movements_ds.get_cash_movement_by_id(
            cash_movement_id
        )
        if result is None:
            return None
        return CashMovementInDb.model_validate(result)

    async def update_cash_movement_by_id(
        self, cash_movement_id: str, cash_movement: UpdateCashMovement
    ) -> CashMovementInDb | None:
        updated_data = cash_movement.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.cash_movements_ds.update_cash_movement_by_id(
            cash_movement_id, updated_data
        )
        if result is None:
            return None
        return CashMovementInDb.model_validate(result)

    async def delete_cash_movement_by_id(
        self, cash_movement_id: str
    ) -> CashMovementInDb | None:
        result = await self.cash_movements_ds.delete_cash_movement_by_id(
            cash_movement_id
        )
        if result is None:
            return None
        return CashMovementInDb.model_validate(result)
