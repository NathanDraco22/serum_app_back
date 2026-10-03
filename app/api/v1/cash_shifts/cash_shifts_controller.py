from fastapi import HTTPException, status

from repos.v1.cash_shifts import (
    CloseCashShift,
    CreateCashShift,
    UpdateCashShift,
    CashShiftInDb,
    CashShiftsRepository,
)
from responses.v1 import ListResponse


class CashShiftsController:
    def __init__(self, cash_shifts_repo: CashShiftsRepository) -> None:
        self.cash_shifts_repo = cash_shifts_repo

    async def open_shift(self, body: CreateCashShift) -> CashShiftInDb:
        return await self.cash_shifts_repo.open_shift(body)

    async def get_current_shift(self, user_id: str) -> CashShiftInDb | None:
        return await self.cash_shifts_repo.get_current_shift(user_id)

    async def close_shift(
        self,
        shift_id: str,
        body: CloseCashShift,
        user_id: str | None = None,
    ) -> CashShiftInDb:
        return await self.cash_shifts_repo.close_shift(
            shift_id=shift_id, close_data=body, user_id=user_id
        )

    async def get_all_cash_shifts(
        self,
        branch_id: str | None = None,
        user_id: str | None = None,
        status_filter: str | None = None,
    ) -> ListResponse[CashShiftInDb]:
        cash_shifts = await self.cash_shifts_repo.get_all_cash_shifts(
            branch_id=branch_id, user_id=user_id, status=status_filter
        )
        return ListResponse(count=len(cash_shifts), data=cash_shifts)

    async def get_cash_shift_by_id(self, cash_shift_id: str) -> CashShiftInDb:
        cash_shift = await self.cash_shifts_repo.get_cash_shift_by_id(cash_shift_id)
        if cash_shift is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash shift not found",
            )
        return cash_shift

    async def update_cash_shift_by_id(
        self, cash_shift_id: str, body: UpdateCashShift
    ) -> CashShiftInDb:
        updated_cash_shift = await self.cash_shifts_repo.update_cash_shift_by_id(
            cash_shift_id, body
        )
        if updated_cash_shift is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash shift not found",
            )
        return updated_cash_shift

    async def delete_cash_shift_by_id(self, cash_shift_id: str) -> CashShiftInDb:
        deleted_cash_shift = await self.cash_shifts_repo.delete_cash_shift_by_id(
            cash_shift_id
        )
        if deleted_cash_shift is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cash shift not found",
            )
        return deleted_cash_shift


cash_shifts_controller = CashShiftsController(
    cash_shifts_repo=CashShiftsRepository.get_instance(),
)
