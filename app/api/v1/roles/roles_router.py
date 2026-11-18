from fastapi import APIRouter, Depends

from app_middleware.depends import auth_middleware, require_admin_user
from serum.repos.v1.roles import CreateRole, RoleInDb, UpdateRole
from responses.v1 import ListResponse

from .roles_controller import roles_controller

roles_router = APIRouter(tags=["rolesV1"])


@roles_router.post("", dependencies=[Depends(require_admin_user)])
async def create_role(body: CreateRole) -> RoleInDb:
    return await roles_controller.create_role(body)


@roles_router.get("", dependencies=[Depends(auth_middleware)])
async def get_all_roles() -> ListResponse[RoleInDb]:
    return await roles_controller.get_all_roles()


@roles_router.get("/{role_id}", dependencies=[Depends(auth_middleware)])
async def get_role_by_id(role_id: str) -> RoleInDb:
    return await roles_controller.get_role_by_id(role_id)


@roles_router.patch("/{role_id}", dependencies=[Depends(require_admin_user)])
async def update_role_by_id(role_id: str, body: UpdateRole) -> RoleInDb:
    return await roles_controller.update_role_by_id(role_id, body)


@roles_router.delete("/{role_id}", dependencies=[Depends(require_admin_user)])
async def delete_role_by_id(role_id: str) -> RoleInDb:
    return await roles_controller.delete_role_by_id(role_id)
