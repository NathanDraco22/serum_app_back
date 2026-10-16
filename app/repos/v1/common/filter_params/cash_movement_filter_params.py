from .base_filter_params import BaseFilterParams


class CashMovementFilterParams(BaseFilterParams):
    shiftId: str | None = None
    branchId: str | None = None
    movementType: str | None = None
    paymentMethod: str | None = None
    startDate: int | None = None
    endDate: int | None = None
