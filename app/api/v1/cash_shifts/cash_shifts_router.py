from fastapi import APIRouter, Query

from serum.repos.v1.cash_shifts import (
    CloseCashShift,
    CreateCashShift,
    UpdateCashShift,
    CashShiftInDb,
)
from responses.v1 import ListResponse

from .cash_shifts_controller import cash_shifts_controller


cash_shifts_router = APIRouter(tags=["cashShiftsV1"])


@cash_shifts_router.post("/open")
async def open_cash_shift(body: CreateCashShift) -> CashShiftInDb:
    return await cash_shifts_controller.open_shift(body)


@cash_shifts_router.get("/current")
async def get_current_cash_shift(user_id: str = Query(...)) -> CashShiftInDb | None:
    return await cash_shifts_controller.get_current_shift(user_id)


@cash_shifts_router.post("/{shift_id}/close")
async def close_cash_shift(
    shift_id: str,
    body: CloseCashShift,
    user_id: str | None = Query(None),
) -> CashShiftInDb:
    return await cash_shifts_controller.close_shift(
        shift_id=shift_id, body=body, user_id=user_id
    )


@cash_shifts_router.get("")
async def get_all_cash_shifts(
    branch_id: str | None = Query(None),
    user_id: str | None = Query(None),
    status: str | None = Query(None),
) -> ListResponse[CashShiftInDb]:
    return await cash_shifts_controller.get_all_cash_shifts(
        branch_id=branch_id,
        user_id=user_id,
        status_filter=status,
    )


@cash_shifts_router.get("/{shift_id}")
async def get_cash_shift_by_id(shift_id: str) -> CashShiftInDb:
    return await cash_shifts_controller.get_cash_shift_by_id(shift_id)


@cash_shifts_router.patch("/{shift_id}")
async def update_cash_shift_by_id(
    shift_id: str, body: UpdateCashShift
) -> CashShiftInDb:
    return await cash_shifts_controller.update_cash_shift_by_id(shift_id, body)


@cash_shifts_router.delete("/{shift_id}")
async def delete_cash_shift_by_id(shift_id: str) -> CashShiftInDb:
    return await cash_shifts_controller.delete_cash_shift_by_id(shift_id)
