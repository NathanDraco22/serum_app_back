from typing import Literal
from pydantic import BaseModel


from repos.v1._shared_models import IncludedTest


OrderStatus = Literal["pending", "completed", "cancelled", "paid", "partiallyPaid"]


class OrderTestResult(IncludedTest):
    resultValue: str | None = None
    alertFlag: str | None = None


class BaseOrder(BaseModel):
    patientId: str
    quotationId: str | None = None
    examId: str
    examName: str
    salePriceApplied: int
    paidAmount: int = 0
    status: OrderStatus = "pending"
    results: list[OrderTestResult] = []


class CreateOrder(BaseOrder):
    pass


class UpdateOrder(BaseModel):
    patientId: str | None = None
    quotationId: str | None = None
    examId: str | None = None
    examName: str | None = None
    salePriceApplied: int | None = None
    paidAmount: int | None = None
    status: str | None = None
    results: list[OrderTestResult] | None = None


class OrderInDb(BaseOrder):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
