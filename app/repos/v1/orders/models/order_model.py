from typing import Literal
from pydantic import BaseModel

from repos.v1._shared_models import IncludedTest

OrderStatus = Literal["pending", "completed", "cancelled", "paid", "partiallyPaid"]


class OrderItem(BaseModel):
    labTestId: str
    name: str
    salePriceApplied: int
    isPack: bool = False


class OrderTestResult(IncludedTest):
    resultValue: str | None = None
    alertFlag: str | None = None


class BaseOrder(BaseModel):
    patientId: str
    doctorId: str | None = None
    quotationId: str | None = None
    items: list[OrderItem] = []
    totalPrice: int = 0
    paidAmount: int = 0
    status: OrderStatus = "pending"
    results: list[OrderTestResult] = []


class CreateOrder(BaseOrder):
    pass


class UpdateOrder(BaseModel):
    patientId: str | None = None
    doctorId: str | None = None
    quotationId: str | None = None
    items: list[OrderItem] | None = None
    totalPrice: int | None = None
    paidAmount: int | None = None
    status: str | None = None
    results: list[OrderTestResult] | None = None


class OrderInDb(BaseOrder):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
