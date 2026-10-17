from pydantic import BaseModel
from serum.repos.v1.common.models.user_info import UserInfo


class BaseReceipt(BaseModel):
    receiptNumber: str | None = None
    orderId: str
    orderNumber: str | None = None
    branchId: str
    shiftId: str | None = None
    registerId: str | None = None
    amount: int
    paymentMethod: str = "cash"
    concept: str = "Pago / Abono de orden"
    performedBy: UserInfo
    patientName: str | None = None


class CreateReceipt(BaseReceipt):
    pass


class UpdateReceipt(BaseModel):
    concept: str | None = None
    patientName: str | None = None


class ReceiptInDb(BaseReceipt):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
