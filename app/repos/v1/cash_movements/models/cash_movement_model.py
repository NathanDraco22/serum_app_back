from pydantic import BaseModel
from repos.v1.common.models.user_info import UserInfo


class BaseCashMovement(BaseModel):
    shiftId: str
    branchId: str
    movementType: str
    paymentMethod: str = "cash"
    amount: int
    concept: str
    performedBy: UserInfo
    resultingBalance: int | None = None
    registerId: str | None = None


class CreateCashMovement(BaseModel):
    shiftId: str
    branchId: str
    movementType: str
    paymentMethod: str = "cash"
    amount: int
    concept: str
    performedBy: UserInfo
    registerId: str | None = None


class UpdateCashMovement(BaseModel):
    concept: str | None = None


class CashMovementInDb(BaseCashMovement):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
