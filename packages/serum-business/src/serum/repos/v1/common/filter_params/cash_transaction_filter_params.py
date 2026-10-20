from .base_filter_params import BaseFilterParams


class CashTransactionFilterParams(BaseFilterParams):
    branchId: str | None = None
    shiftId: str | None = None
    registerId: str | None = None
    flowType: str | None = None
    subType: str | None = None
    paymentMethod: str | None = None
    startDate: int | None = None
    endDate: int | None = None
