from pydantic import BaseModel

from serum.repos.v1.common.models.user_info import UserInfo


class BioanalystInfo(BaseModel):
    name: str
    title: str
    code: str
    sealUrl: str | None = None


# Alias retrocompatible
BranchBioanalyst = BioanalystInfo


class AuxBioanalyst(BaseModel):
    user: UserInfo
    bioanalyst: BioanalystInfo


class BaseBranch(BaseModel):
    name: str
    address: str
    phone: str
    email: str | None = None
    facebook: str | None = None
    logoUrl: str | None = None
    imageUrl: str | None = None
    isoLogoUrl: str | None = None
    bioanalyst: BioanalystInfo | None = None
    auxBio: list[AuxBioanalyst] = []


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
    bioanalyst: BioanalystInfo | None = None
    auxBio: list[AuxBioanalyst] | None = None


class BranchInDb(BaseBranch):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
