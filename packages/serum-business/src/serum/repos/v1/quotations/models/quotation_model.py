from pydantic import BaseModel

from serum.repos.v1.orders.models.order_model import DoctorInfo, PatientInfo


class QuotedItem(BaseModel):
    labTestId: str
    name: str
    quotedPrice: int
    isPack: bool = False
    priceLevel: int = 1


class BaseQuotation(BaseModel):
    branchId: str
    clientName: str = "Cliente General"
    patientId: str | None = None
    clientInfo: PatientInfo | None = None
    doctorId: str | None = None
    doctorInfo: DoctorInfo | None = None
    items: list[QuotedItem] = []
    totalAmount: int = 0
    status: str = "pending"
    convertedToOrderId: str | None = None


class CreateQuotation(BaseQuotation):
    pass


class UpdateQuotation(BaseModel):
    branchId: str | None = None
    clientName: str | None = None
    patientId: str | None = None
    clientInfo: PatientInfo | None = None
    doctorId: str | None = None
    doctorInfo: DoctorInfo | None = None
    items: list[QuotedItem] | None = None
    totalAmount: int | None = None
    status: str | None = None
    convertedToOrderId: str | None = None


class QuotationInDb(BaseQuotation):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
