from fastapi import HTTPException, status

from repos.v1.roles import (
    CreateRole,
    RoleInDb,
    RolesRepository,
    UpdateRole,
)
from responses.v1 import ListResponse


class RolesController:
    def __init__(self, roles_repo: RolesRepository) -> None:
        self.roles_repo = roles_repo

    async def create_role(self, body: CreateRole) -> RoleInDb:
        existing = await self.roles_repo.get_role_by_name(body.name.strip())
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un rol con el nombre '{body.name}'.",
            )
        return await self.roles_repo.create_role(body)

    async def get_all_roles(self) -> ListResponse[RoleInDb]:
        roles = await self.roles_repo.get_all_roles()
        return ListResponse(
            data=roles,
            count=len(roles),
        )

    async def get_role_by_id(self, role_id: str) -> RoleInDb:
        role = await self.roles_repo.get_role_by_id(role_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado",
            )
        return role

    async def update_role_by_id(self, role_id: str, body: UpdateRole) -> RoleInDb:
        if body.name is not None:
            existing = await self.roles_repo.get_role_by_name(body.name.strip())
            if existing is not None and existing.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya existe otro rol con el nombre '{body.name}'.",
                )

        updated_role = await self.roles_repo.update_role_by_id(role_id, body)
        if updated_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado",
            )
        return updated_role

    async def delete_role_by_id(self, role_id: str) -> RoleInDb:
        role = await self.roles_repo.get_role_by_id(role_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado",
            )
        if role.name.lower() == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol Admin principal no puede ser eliminado.",
            )

        deleted_role = await self.roles_repo.delete_role_by_id(role_id)
        if deleted_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado",
            )
        return deleted_role


roles_controller = RolesController(
    roles_repo=RolesRepository.get_instance(),
)
