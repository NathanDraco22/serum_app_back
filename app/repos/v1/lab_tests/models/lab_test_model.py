from pydantic import BaseModel

from repos.v1._shared_models import ReferenceValue


class BaseLabTest(BaseModel):
    parameterName: str
    medicalClassification: str
    dataType: str
    unitOfMeasure: str
    referenceValues: list[ReferenceValue] = []


class CreateLabTest(BaseLabTest):
    pass


class UpdateLabTest(BaseModel):
    parameterName: str | None = None
    medicalClassification: str | None = None
    dataType: str | None = None
    unitOfMeasure: str | None = None
    referenceValues: list[ReferenceValue] | None = None


class LabTestInDb(BaseLabTest):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
