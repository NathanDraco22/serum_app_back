from fastapi import APIRouter, Depends

from app_middleware.depends import auth_middleware, require_admin_user
from serum.repos.v1.users import CreateUser, UpdateUser, UserInDb
from responses.v1 import ListResponse

from .users_controller import users_controller

users_router = APIRouter(tags=["usersV1"])


@users_router.post("", dependencies=[Depends(require_admin_user)])
async def create_user(body: CreateUser) -> UserInDb:
    return await users_controller.create_user(body)


@users_router.get("", dependencies=[Depends(auth_middleware)])
async def get_all_users() -> ListResponse[UserInDb]:
    return await users_controller.get_all_users()


@users_router.get("/{user_id}", dependencies=[Depends(auth_middleware)])
async def get_user_by_id(user_id: str) -> UserInDb:
    return await users_controller.get_user_by_id(user_id)


@users_router.patch("/{user_id}")
async def update_user_by_id(
    user_id: str,
    body: UpdateUser,
    current_user: UserInDb = Depends(require_admin_user),
) -> UserInDb:
    return await users_controller.update_user_by_id(
        user_id,
        body,
        actor=current_user,
    )


@users_router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: str,
    current_user: UserInDb = Depends(require_admin_user),
) -> UserInDb:
    return await users_controller.delete_user_by_id(
        user_id,
        actor=current_user,
    )
