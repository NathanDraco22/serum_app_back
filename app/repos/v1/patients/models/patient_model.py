from pydantic import BaseModel


class BasePatient(BaseModel):
    name: str
    dateOfBirth: int
    gender: str
    phone: str
    address: str
    email: str | None = None


class CreatePatient(BasePatient):
    pass


class UpdatePatient(BaseModel):
    name: str | None = None
    dateOfBirth: int | None = None
    gender: str | None = None
    phone: str | None = None
    address: str | None = None
    email: str | None = None


class PatientInDb(BasePatient):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
