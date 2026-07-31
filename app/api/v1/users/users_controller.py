from fastapi import HTTPException, status

from repos.v1.users import (
    CreateUser,
    DuplicateUserError,
    UpdateUser,
    UserInDb,
    UsersRepository,
)
from responses.v1 import ListResponse


class UsersController:
    def __init__(self, users_repo: UsersRepository) -> None:
        self.users_repo = users_repo

    async def create_user(self, body: CreateUser) -> UserInDb:
        try:
            return await self.users_repo.create_user(body)
        except DuplicateUserError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

    async def get_all_users(self) -> ListResponse[UserInDb]:
        users = await self.users_repo.get_all_users()
        return ListResponse(count=len(users), data=users)

    async def get_user_by_id(self, user_id: str) -> UserInDb:
        user = await self.users_repo.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def update_user_by_id(self, user_id: str, body: UpdateUser) -> UserInDb:
        updated_user = await self.users_repo.update_user_by_id(user_id, body)
        if updated_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return updated_user

    async def delete_user_by_id(self, user_id: str) -> UserInDb:
        deleted_user = await self.users_repo.delete_user_by_id(user_id)
        if deleted_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return deleted_user


users_controller = UsersController(
    users_repo=UsersRepository.get_instance(),
)
