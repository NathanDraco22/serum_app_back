from .base_filter_params import BaseFilterParams


class OrderFilterParams(BaseFilterParams):
    branchId: str | None = None
    patientId: str | None = None
    doctorId: str | None = None
    status: str | None = None
    startDate: int | None = None
    endDate: int | None = None
