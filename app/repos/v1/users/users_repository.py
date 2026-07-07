from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool

from .data.users_datasource import UsersDataSource
from .models.user_model import CreateUser, UpdateUser, UserInDb


class UsersRepository:
    _instance: "UsersRepository|None" = None

    def __init__(self, users_ds: UsersDataSource):
        self.users_ds = users_ds

    @classmethod
    def get_instance(cls) -> "UsersRepository":
        if cls._instance is None:
            cls._instance = cls(UsersDataSource())
        return cls._instance

    async def create_user(self, create_user: CreateUser) -> UserInDb:
        new_user = UserInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            **create_user.model_dump(),
        )
        result = await self.users_ds.create_user(new_user.model_dump())
        return UserInDb.model_validate(result)

    async def get_all_users(self) -> list[UserInDb]:
        results = await self.users_ds.get_all_users()
        return [UserInDb.model_validate(r) for r in results]

    async def get_user_by_id(self, user_id: str) -> UserInDb | None:
        result = await self.users_ds.get_user_by_id(user_id)
        if result is None:
            return None
        return UserInDb.model_validate(result)

    async def update_user_by_id(
        self, user_id: str, user: UpdateUser
    ) -> UserInDb | None:
        updated_data = user.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.users_ds.update_user_by_id(user_id, updated_data)
        if result is None:
            return None
        return UserInDb.model_validate(result)

    async def delete_user_by_id(self, user_id: str) -> UserInDb | None:
        result = await self.users_ds.delete_user_by_id(user_id)
        if result is None:
            return None
        return UserInDb.model_validate(result)
