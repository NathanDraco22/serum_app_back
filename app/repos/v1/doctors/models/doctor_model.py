from pydantic import BaseModel


class BaseDoctor(BaseModel):
    name: str
    specialty: str
    phone: str
    email: str | None = None


class CreateDoctor(BaseDoctor):
    pass


class UpdateDoctor(BaseModel):
    name: str | None = None
    specialty: str | None = None
    phone: str | None = None
    email: str | None = None


class DoctorInDb(BaseDoctor):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
