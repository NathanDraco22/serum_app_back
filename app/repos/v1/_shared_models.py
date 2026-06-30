from pydantic import BaseModel


class ReferenceValue(BaseModel):
    patientType: str
    gender: str
    minAgeDays: int
    maxAgeDays: int
    minValue: float
    maxValue: float


class IncludedTest(BaseModel):
    labTestId: str
    parameterName: str
    medicalClassification: str
    dataType: str
    unitOfMeasure: str
    referenceValues: list[ReferenceValue] = []
