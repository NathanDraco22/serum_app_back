from serum.core.default_values.root_constants import ROOT_USER_ID, ROOT_USERNAME
from serum.core.security import SysPasswordHasher
from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool

from .data.users_datasource import UsersDataSource
from .models.user_model import CreateUser, UpdateUser, UserInDb


class DuplicateUserError(Exception):
    pass


class ProtectedUserError(Exception):
    pass


class SelfUserOperationError(Exception):
    pass


class LastAdminError(Exception):
    pass


def _is_root_or_internal(user: UserInDb) -> bool:
    return (
        user.id == ROOT_USER_ID
        or user.isInternal
        or user.username.lower() in {ROOT_USERNAME.lower(), "root"}
    )


def _is_admin_values(role: str | None, access_level: int | None) -> bool:
    return (
        (access_level is not None and access_level >= 5)
        or (role or "").lower() in {"admin", "administrador"}
    )


def _is_admin_user(user: UserInDb) -> bool:
    return _is_root_or_internal(user) or _is_admin_values(
        user.role, user.accessLevel
    )


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

    async def _count_other_active_admins(self, user_id: str) -> int:
        results = await self.users_ds.get_all_users(include_internal=True)
        users = [UserInDb.model_validate(r) for r in results]
        return sum(
            1
            for user in users
            if user.id != user_id
            and user.isActive
            and not user.isDeleted
            and _is_admin_user(user)
        )

    async def update_user_by_id(
        self, user_id: str, user: UpdateUser, actor_id: str | None = None
    ) -> UserInDb | None:
        existing = await self.get_user_by_id(user_id)
        if existing is None:
            return None

        if _is_root_or_internal(existing):
            raise ProtectedUserError("El usuario root del sistema no puede modificarse")

        updated_data = user.model_dump(exclude_unset=True)

        # La pertenencia al sistema interno no se modifica desde la API.
        updated_data.pop("isInternal", None)
        for field in ("username", "name", "role", "accessLevel", "isActive"):
            if field in updated_data and updated_data[field] is None:
                updated_data.pop(field)

        if "username" in updated_data:
            updated_data["username"] = str(updated_data["username"]).strip()

        for field in ("email", "phone"):
            value = updated_data.get(field)
            if isinstance(value, str) and not value.strip():
                updated_data[field] = None

        if "password" in updated_data:
            password = updated_data["password"]
            if not password:
                updated_data.pop("password")
            else:
                updated_data["password"] = SysPasswordHasher.hash_password(password)

        if actor_id == user_id:
            if updated_data.get("isActive") is False:
                raise SelfUserOperationError("No puedes desactivar tu propia cuenta")
            if "role" in updated_data or "accessLevel" in updated_data:
                next_role = updated_data.get("role", existing.role)
                next_access_level = updated_data.get(
                    "accessLevel", existing.accessLevel
                )
                if not _is_admin_values(next_role, next_access_level):
                    raise SelfUserOperationError(
                        "No puedes quitarte tu propio rol de administrador"
                    )

        will_be_active_admin = bool(
            updated_data.get("isActive", existing.isActive)
        ) and _is_admin_values(
            updated_data.get("role", existing.role),
            updated_data.get("accessLevel", existing.accessLevel),
        )
        if (
            existing.isActive
            and _is_admin_user(existing)
            and not will_be_active_admin
            and await self._count_other_active_admins(user_id) == 0
        ):
            raise LastAdminError(
                "Debe existir al menos un administrador activo en el sistema"
            )

        if updated_data.get("username"):
            duplicate = await self.get_user_by_username(
                str(updated_data["username"])
            )
            if duplicate is not None and duplicate.id != user_id:
                raise DuplicateUserError("Username already exists")

        if updated_data.get("email"):
            duplicate = await self.get_user_by_email(str(updated_data["email"]))
            if duplicate is not None and duplicate.id != user_id:
                raise DuplicateUserError("Email already exists")

        if updated_data.get("phone"):
            duplicate = await self.get_user_by_phone(str(updated_data["phone"]))
            if duplicate is not None and duplicate.id != user_id:
                raise DuplicateUserError("Phone already exists")

        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.users_ds.update_user_by_id(user_id, updated_data)
        if result is None:
            return None
        return UserInDb.model_validate(result)

    async def delete_user_by_id(
        self, user_id: str, actor_id: str | None = None
    ) -> UserInDb | None:
        existing = await self.get_user_by_id(user_id)
        if existing is None:
            return None

        if _is_root_or_internal(existing):
            raise ProtectedUserError("El usuario root del sistema no puede eliminarse")

        if actor_id == user_id:
            raise SelfUserOperationError("No puedes eliminar tu propia cuenta")

        if (
            existing.isActive
            and _is_admin_user(existing)
            and await self._count_other_active_admins(user_id) == 0
        ):
            raise LastAdminError(
                "Debe existir al menos un administrador activo en el sistema"
            )

        result = await self.users_ds.delete_user_by_id(user_id)
        if result is None:
            return None
        return UserInDb.model_validate(result)
