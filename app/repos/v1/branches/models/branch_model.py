from pydantic import BaseModel


class BaseBranch(BaseModel):
    name: str
    address: str
    phone: str


class CreateBranch(BaseBranch):
    pass


class UpdateBranch(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None


class BranchInDb(BaseBranch):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
