from pydantic import BaseModel


class QuotedItem(BaseModel):
    labTestId: str
    name: str
    quotedPrice: int
    isPack: bool = False


class BaseQuotation(BaseModel):
    clientName: str
    patientId: str | None = None
    items: list[QuotedItem] = []
    totalAmount: int = 0
    status: str = "pending"
    convertedToOrderId: str | None = None


class CreateQuotation(BaseQuotation):
    pass


class UpdateQuotation(BaseModel):
    clientName: str | None = None
    patientId: str | None = None
    items: list[QuotedItem] | None = None
    totalAmount: int | None = None
    status: str | None = None
    convertedToOrderId: str | None = None


class QuotationInDb(BaseQuotation):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
