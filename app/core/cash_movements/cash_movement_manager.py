from repos.v1.cash_movements.models.cash_movement_model import (
    CashMovementInDb,
    CreateCashMovement,
)
from .process_cash_movement import process_cash_movement
from .process_cancel_cash_movement import process_cancel_cash_movement


class CashMovementManager:
    async def process_movement(
        self, create_movement: CreateCashMovement
    ) -> CashMovementInDb:
        return await process_cash_movement(create_movement)

    async def cancel_movement(
        self, cash_movement_id: str
    ) -> CashMovementInDb:
        return await process_cancel_cash_movement(cash_movement_id)

