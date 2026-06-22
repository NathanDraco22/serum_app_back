from fastapi import APIRouter

from repos.v1.users import CreateUser, UpdateUser, UserInDb
from responses.v1 import ListResponse

from .users_controller import users_controller


users_router = APIRouter(tags=["usersV1"])


@users_router.post("")
async def create_user(body: CreateUser) -> UserInDb:
    return await users_controller.create_user(body)


@users_router.get("")
async def get_all_users() -> ListResponse[UserInDb]:
    return await users_controller.get_all_users()


@users_router.get("/{user_id}")
async def get_user_by_id(user_id: str) -> UserInDb:
    return await users_controller.get_user_by_id(user_id)


@users_router.patch("/{user_id}")
async def update_user_by_id(user_id: str, body: UpdateUser) -> UserInDb: 
    return await users_controller.update_user_by_id(user_id, body)


@users_router.delete("/{user_id}")
async def delete_user_by_id(user_id: str) -> UserInDb:
    return await users_controller.delete_user_by_id(user_id)
