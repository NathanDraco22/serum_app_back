from pydantic import BaseModel


class BranchBioanalyst(BaseModel):
    name: str
    title: str
    code: str


class BaseBranch(BaseModel):
    name: str
    address: str
    phone: str
    email: str | None = None
    facebook: str | None = None
    logoUrl: str | None = None
    imageUrl: str | None = None
    isoLogoUrl: str | None = None
    bioanalyst: BranchBioanalyst | None = None


class CreateBranch(BaseBranch):
    pass


class UpdateBranch(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    facebook: str | None = None
    logoUrl: str | None = None
    imageUrl: str | None = None
    isoLogoUrl: str | None = None
    bioanalyst: BranchBioanalyst | None = None


class BranchInDb(BaseBranch):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
