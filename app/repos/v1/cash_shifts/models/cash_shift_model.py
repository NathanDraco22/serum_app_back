from pydantic import BaseModel


class BaseCashShift(BaseModel):
    userId: str
    branchId: str
    notes: str = ""
    userName: str | None = None
    branchName: str | None = None


class CreateCashShift(BaseCashShift):
    initialBalance: int


class CloseCashShift(BaseModel):
    declaredCash: int
    notes: str = ""


class UpdateCashShift(BaseModel):
    notes: str | None = None


class CashShiftInDb(BaseCashShift):
    id: str
    status: str = "OPEN"
    openedAt: int
    closedAt: int | None = None
    initialBalance: int
    cashBalance: int = 0
    cardBalance: int = 0
    transferBalance: int = 0
    totalBalance: int = 0
    declaredCash: int | None = None
    difference: int | None = None
    isDeleted: bool = False
    createdAt: int
    updatedAt: int | None = None
