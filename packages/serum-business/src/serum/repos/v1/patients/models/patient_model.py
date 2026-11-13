from pydantic import BaseModel, field_validator, model_validator


class BasePatient(BaseModel):
    name: str
    dateOfBirth: int
    gender: str
    phone: str
    address: str | None = None
    email: str | None = None
    cardId: str | None = None
    originBranch: str
    age: int | None = None


class CreatePatient(BasePatient):
    @field_validator("dateOfBirth")
    @classmethod
    def validate_date_of_birth(cls, value: int) -> int:
        if value < 0:
            raise ValueError("La fecha de nacimiento no puede ser negativa")
        return value

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: int | None) -> int | None:
        if value is not None and (value < 0 or value > 130):
            raise ValueError("La edad debe estar entre 0 y 130 años")
        return value

    @model_validator(mode="after")
    def validate_demographics(self) -> "CreatePatient":
        if self.dateOfBirth <= 0 and self.age is None:
            raise ValueError(
                "La fecha de nacimiento o la edad son obligatorias para el paciente"
            )
        return self


class UpdatePatient(BaseModel):
    name: str | None = None
    dateOfBirth: int | None = None
    gender: str | None = None
    phone: str | None = None
    address: str | None = None
    email: str | None = None
    cardId: str | None = None
    originBranch: str | None = None
    age: int | None = None

    @field_validator("dateOfBirth")
    @classmethod
    def validate_date_of_birth(cls, value: int | None) -> int:
        if value is None or value <= 0:
            raise ValueError("La fecha de nacimiento no puede vaciarse")
        return value

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: int | None) -> int | None:
        if value is not None and (value < 0 or value > 130):
            raise ValueError("La edad debe estar entre 0 y 130 años")
        return value


class PatientInDb(BasePatient):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
