from pydantic import BaseModel


class BaseDoctor(BaseModel):
    name: str
    specialty: str
    phone: str | None = None
    email: str | None = None
    cardId: str | None = None
    originBranch: str


class CreateDoctor(BaseDoctor):
    pass


class UpdateDoctor(BaseModel):
    name: str | None = None
    specialty: str | None = None
    phone: str | None = None
    email: str | None = None
    cardId: str | None = None
    originBranch: str | None = None


class DoctorInDb(BaseDoctor):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
