from pydantic import BaseModel

from repos.v1._shared_models import ReferenceValue


class BaseLabTest(BaseModel):
    name: str
    code: str | None = None
    commercialCategory: str = ""
    salePrice: int = 0
    salePrice2: int = 0
    currency: str = "USD"
    isPack: bool = False
    childTestIds: list[str] = []
    dataType: str = "numeric"
    unitOfMeasure: str = ""
    referenceValues: list[ReferenceValue] = []
    qualitativeOptions: list[str] = []
    expectedQualitativeValue: str | None = None


class CreateLabTest(BaseLabTest):
    pass


class UpdateLabTest(BaseModel):
    name: str | None = None
    code: str | None = None
    commercialCategory: str | None = None
    salePrice: int | None = None
    salePrice2: int | None = None
    currency: str | None = None
    isPack: bool | None = None
    childTestIds: list[str] | None = None
    dataType: str | None = None
    unitOfMeasure: str | None = None
    referenceValues: list[ReferenceValue] | None = None
    qualitativeOptions: list[str] | None = None
    expectedQualitativeValue: str | None = None


class LabTestInDb(BaseLabTest):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
