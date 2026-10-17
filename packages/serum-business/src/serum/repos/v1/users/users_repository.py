from serum.core.security import SysPasswordHasher
from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool

from .data.users_datasource import UsersDataSource
from .models.user_model import CreateUser, UpdateUser, UserInDb


class DuplicateUserError(Exception):
    pass


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
        if create_user.username:
            existing = await self.users_ds.get_user_by_username(
                create_user.username
            )
            if existing:
                raise DuplicateUserError("Username already exists")

        if create_user.email:
            existing = await self.users_ds.get_user_by_email(create_user.email)
            if existing:
                raise DuplicateUserError("Email already exists")

        if create_user.phone:
            existing = await self.users_ds.get_user_by_phone(create_user.phone)
            if existing:
                raise DuplicateUserError("Phone already exists")

        hashed_password = SysPasswordHasher.hash_password(create_user.password)

        new_user = UserInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            **create_user.model_dump(exclude={"password"}),
            password=hashed_password,
        )
        result = await self.users_ds.create_user(new_user.model_dump())
        return UserInDb.model_validate(result)

    async def get_user_by_username(self, username: str) -> UserInDb | None:
        result = await self.users_ds.get_user_by_username(username)
        if result is None:
            return None
        return UserInDb.model_validate(result)

    async def get_user_by_email(self, email: str) -> UserInDb | None:
        result = await self.users_ds.get_user_by_email(email)
        if result is None:
            return None
        return UserInDb.model_validate(result)

    async def get_user_by_phone(self, phone: str) -> UserInDb | None:
        result = await self.users_ds.get_user_by_phone(phone)
        if result is None:
            return None
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

        if "password" in updated_data and updated_data["password"] is not None:
            updated_data["password"] = SysPasswordHasher.hash_password(
                updated_data["password"]
            )

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
