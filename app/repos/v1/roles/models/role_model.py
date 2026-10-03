from pydantic import BaseModel


class BaseRole(BaseModel):
    name: str
    accessLevel: int = 3
    description: str | None = None


class CreateRole(BaseRole):
    pass


class UpdateRole(BaseModel):
    name: str | None = None
    accessLevel: int | None = None
    description: str | None = None


class RoleInDb(BaseRole):
    id: str
    createdAt: int
    updatedAt: int | None = None
    isDeleted: bool = False
