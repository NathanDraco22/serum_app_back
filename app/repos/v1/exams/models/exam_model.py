from pydantic import BaseModel

from repos.v1._shared_models import IncludedTest


class BaseExam(BaseModel):
    name: str
    commercialCategory: str
    salePrice: float
    currency: str
    includedTests: list[IncludedTest] = []


class CreateExam(BaseExam):
    pass


class UpdateExam(BaseModel):
    name: str | None = None
    commercialCategory: str | None = None
    salePrice: float | None = None
    currency: str | None = None
    includedTests: list[IncludedTest] | None = None


class ExamInDb(BaseExam):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
