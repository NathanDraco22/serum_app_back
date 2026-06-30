from pydantic import BaseModel


class QuotedExam(BaseModel):
    examId: str
    examName: str
    quotedPrice: int


class BaseQuotation(BaseModel):
    clientName: str
    patientId: str | None = None
    exams: list[QuotedExam] = []
    totalAmount: int
    status: str = "pending"
    convertedToOrderId: str | None = None


class CreateQuotation(BaseQuotation):
    pass


class UpdateQuotation(BaseModel):
    clientName: str | None = None
    patientId: str | None = None
    exams: list[QuotedExam] | None = None
    totalAmount: int | None = None
    status: str | None = None
    convertedToOrderId: str | None = None


class QuotationInDb(BaseQuotation):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
