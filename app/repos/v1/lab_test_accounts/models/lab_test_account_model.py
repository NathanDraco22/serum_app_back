from pydantic import BaseModel


class LabTestCommercial(BaseModel):
    salePrice: int = 0
    salePrice2: int = 0
    costPrice: int = 0
    currency: str = "USD"


class BaseLabTestAccount(BaseModel):
    branchId: str
    labTestId: str
    commercial: LabTestCommercial


class CreateLabTestAccount(BaseLabTestAccount):
    pass


class UpdateLabTestAccountCommercial(BaseModel):
    salePrice: int | None = None
    salePrice2: int | None = None
    costPrice: int | None = None
    currency: str | None = None


class LabTestAccountInDb(BaseLabTestAccount):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
