from pydantic import BaseModel


class ReferenceValue(BaseModel):
    patientType: str
    gender: str
    minAgeDays: int
    maxAgeDays: int
    minValue: float
    maxValue: float
    useAge: bool = False
    useGender: bool = False


class IncludedTest(BaseModel):
    labTestId: str
    parameterName: str
    medicalClassification: str = ""
    subclassification: str = ""
    dataType: str
    unitOfMeasure: str = ""
    referenceValues: list[ReferenceValue] = []
    qualitativeOptions: list[str] = []
    expectedQualitativeValue: str | None = None
    referenceText: str = ""
    parentExamName: str | None = None
