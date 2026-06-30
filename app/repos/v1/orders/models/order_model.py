from pydantic import BaseModel

from repos.v1._shared_models import IncludedTest


class OrderTestResult(IncludedTest):
    resultValue: str | None = None
    alertFlag: str | None = None


class BaseOrder(BaseModel):
    patientId: str
    quotationId: str | None = None
    examId: str
    examName: str
    salePriceApplied: float
    status: str = "pending"
    results: list[OrderTestResult] = []


class CreateOrder(BaseOrder):
    pass


class UpdateOrder(BaseModel):
    patientId: str | None = None
    quotationId: str | None = None
    examId: str | None = None
    examName: str | None = None
    salePriceApplied: float | None = None
    status: str | None = None
    results: list[OrderTestResult] | None = None


class OrderInDb(BaseOrder):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
