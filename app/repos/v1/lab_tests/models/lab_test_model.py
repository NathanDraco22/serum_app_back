from pydantic import BaseModel

from repos.v1._shared_models import ReferenceValue
from repos.v1.lab_test_accounts.models.lab_test_account_model import LabTestCommercial


class BaseLabTest(BaseModel):
    name: str
    code: str | None = None
    commercialCategory: str = ""
    salePrice: int = 0
    salePrice2: int = 0
    currency: str = "USD"
    isPack: bool = False
    useChildTestsPriceSum: bool = True
    childTestIds: list[str] = []
    dataType: str = "numeric"
    unitOfMeasure: str = ""
    referenceValues: list[ReferenceValue] = []
    qualitativeOptions: list[str] = []
    expectedQualitativeValue: str | None = None


class CreateLabTest(BaseLabTest):
    branchId: str
    costPrice: int = 0


class UpdateLabTest(BaseModel):
    branchId: str | None = None
    name: str | None = None
    code: str | None = None
    commercialCategory: str | None = None
    salePrice: int | None = None
    salePrice2: int | None = None
    costPrice: int | None = None
    currency: str | None = None
    isPack: bool | None = None
    useChildTestsPriceSum: bool | None = None
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
    costPrice: int = 0
    commercial: LabTestCommercial | None = None

