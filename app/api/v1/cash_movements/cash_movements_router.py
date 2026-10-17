from fastapi import APIRouter, Depends

from serum.repos.v1.cash_movements import (
    CashMovementInDb,
    CreateCashMovement,
    UpdateCashMovement,
)
from serum.repos.v1.common.filter_params import CashMovementFilterParams
from responses.v1 import ListResponse

from .cash_movements_controller import cash_movements_controller

cash_movements_router = APIRouter(tags=["cashMovementsV1"])


@cash_movements_router.post("")
async def create_cash_movement(body: CreateCashMovement) -> CashMovementInDb:
    return await cash_movements_controller.create_cash_movement(body)


@cash_movements_router.get("")
async def get_all_cash_movements(
    query_params: CashMovementFilterParams = Depends(),
) -> ListResponse[CashMovementInDb]:
    return await cash_movements_controller.get_all_cash_movements(query_params)


@cash_movements_router.get("/{cash_movement_id}")
async def get_cash_movement_by_id(cash_movement_id: str) -> CashMovementInDb:
    return await cash_movements_controller.get_cash_movement_by_id(
        cash_movement_id
    )


@cash_movements_router.patch("/{cash_movement_id}")
async def update_cash_movement_by_id(
    cash_movement_id: str, body: UpdateCashMovement
) -> CashMovementInDb:
    return await cash_movements_controller.update_cash_movement_by_id(
        cash_movement_id, body
    )


@cash_movements_router.delete("/{cash_movement_id}")
async def delete_cash_movement_by_id(
    cash_movement_id: str,
) -> CashMovementInDb:
    return await cash_movements_controller.delete_cash_movement_by_id(
        cash_movement_id
    )
