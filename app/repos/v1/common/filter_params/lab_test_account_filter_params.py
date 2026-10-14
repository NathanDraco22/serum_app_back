from .base_filter_params import BaseFilterParams


class LabTestAccountFilterParams(BaseFilterParams):
    branchId: str | None = None
    labTestId: str | None = None
