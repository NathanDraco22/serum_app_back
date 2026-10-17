from typing import Any
from pydantic import BaseModel, field_validator


class LabTestCommercial(BaseModel):
    salePrice: int = 0
    salePrice2: int = 0
    costPrice: int = 0
    currency: str = "USD"

    @field_validator("salePrice", "salePrice2", "costPrice", mode="before")
    @classmethod
    def default_int_if_none(cls, v: Any) -> int:
        if v is None:
            return 0
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    @field_validator("currency", mode="before")
    @classmethod
    def default_currency_if_none(cls, v: Any) -> str:
        return "USD" if not v else str(v)


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
