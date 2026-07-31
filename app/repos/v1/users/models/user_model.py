from pydantic import BaseModel


class BaseUser(BaseModel):
    username: str
    password: str
    name: str
    email: str | None = None
    phone: str | None = None
    role: str
    branches: list[str] = []
    isActive: bool = True


class CreateUser(BaseUser):
    pass


class UpdateUser(BaseModel):
    username: str | None = None
    password: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    branches: list[str] | None = None
    isActive: bool | None = None


class UserInDb(BaseUser):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
