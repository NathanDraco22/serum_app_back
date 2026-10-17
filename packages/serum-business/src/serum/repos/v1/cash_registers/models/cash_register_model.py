from pydantic import BaseModel
from serum.repos.v1.common.models.user_info import UserInfo


class BaseCashRegister(BaseModel):
    branchId: str
    name: str
    isOpen: bool = False
    cashBalance: int = 0
    cardBalance: int = 0
    transferBalance: int = 0
    totalBalance: int = 0
    openedBy: UserInfo | None = None


class CreateCashRegister(BaseCashRegister):
    pass


class UpdateCashRegister(BaseModel):
    name: str | None = None
    isOpen: bool | None = None
    cashBalance: int | None = None
    cardBalance: int | None = None
    transferBalance: int | None = None
    totalBalance: int | None = None
    openedBy: UserInfo | None = None


class CashRegisterInDb(BaseCashRegister):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
