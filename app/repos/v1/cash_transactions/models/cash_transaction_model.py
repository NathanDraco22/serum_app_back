from pydantic import BaseModel
from repos.v1.common.models.user_info import UserInfo


class BaseCashTransaction(BaseModel):
    registerId: str
    branchId: str
    flowType: str
    subType: str
    paymentMethod: str | None = None
    amount: int
    resultingBalance: int
    concept: str
    referenceId: str | None = None
    performedBy: UserInfo


class CreateCashTransaction(BaseCashTransaction):
    pass


class UpdateCashTransaction(BaseModel):
    paymentMethod: str | None = None
    concept: str | None = None


class CashTransactionInDb(BaseCashTransaction):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
