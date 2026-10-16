from fastapi import HTTPException, status

from core.cash_movements import CashMovementManager
from repos.v1.cash_movements import (
    CashMovementInDb,
    CashMovementsRepository,
    CreateCashMovement,
    UpdateCashMovement,
)
from repos.v1.common.filter_params import CashMovementFilterParams
from responses.v1 import ListResponse


class CashMovementsController:
    def __init__(
        self,
        cash_movements_repo: CashMovementsRepository,
        cash_movement_manager: CashMovementManager | None = None,
    ) -> None:
        self.cash_movements_repo = cash_movements_repo
        self.cash_movement_manager = (
            cash_movement_manager or CashMovementManager()
        )

    async def create_cash_movement(
        self, body: CreateCashMovement
    ) -> CashMovementInDb:
        return await self.cash_movement_manager.process_movement(body)

    async def get_all_cash_movements(
        self, query_params: CashMovementFilterParams | None = None
    ) -> ListResponse[CashMovementInDb]:
        cash_movements = await self.cash_movements_repo.get_all_cash_movements(
            query_params
        )
        return ListResponse(count=len(cash_movements), data=cash_movements)

    async def get_cash_movement_by_id(
        self, cash_movement_id: str
    ) -> CashMovementInDb:
        cash_movement = await self.cash_movements_repo.get_cash_movement_by_id(
            cash_movement_id
        )
        if cash_movement is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash movement not found",
            )
        return cash_movement

    async def update_cash_movement_by_id(
        self, cash_movement_id: str, body: UpdateCashMovement
    ) -> CashMovementInDb:
        updated_cash_movement = (
            await self.cash_movements_repo.update_cash_movement_by_id(
                cash_movement_id, body
            )
        )
        if updated_cash_movement is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash movement not found",
            )
        return updated_cash_movement

    async def delete_cash_movement_by_id(
        self, cash_movement_id: str
    ) -> CashMovementInDb:
        return await self.cash_movement_manager.cancel_movement(
            cash_movement_id
        )


cash_movements_controller = CashMovementsController(
    cash_movements_repo=CashMovementsRepository.get_instance(),
)

