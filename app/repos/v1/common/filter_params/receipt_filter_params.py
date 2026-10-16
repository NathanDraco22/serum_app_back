from .base_filter_params import BaseFilterParams


class ReceiptFilterParams(BaseFilterParams):
    orderId: str | None = None
    branchId: str | None = None
    shiftId: str | None = None
    registerId: str | None = None
    paymentMethod: str | None = None
    startDate: int | None = None
    endDate: int | None = None
