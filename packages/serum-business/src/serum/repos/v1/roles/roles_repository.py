from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool

from .data.roles_datasource import RolesDataSource
from .models.role_model import CreateRole, RoleInDb, UpdateRole


class RolesRepository:
    _instance: "RolesRepository|None" = None

    def __init__(self, roles_ds: RolesDataSource):
        self.roles_ds = roles_ds

    @classmethod
    def get_instance(cls) -> "RolesRepository":
        if cls._instance is None:
            cls._instance = cls(RolesDataSource())
        return cls._instance

    async def create_role(self, create_role: CreateRole) -> RoleInDb:
        new_role = RoleInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            isDeleted=False,
            **create_role.model_dump(),
        )
        result = await self.roles_ds.create_role(new_role.model_dump())
        return RoleInDb.model_validate(result)

    async def get_all_roles(self) -> list[RoleInDb]:
        results = await self.roles_ds.get_all_roles()
        return [RoleInDb.model_validate(result) for result in results]

    async def get_role_by_id(self, role_id: str) -> RoleInDb | None:
        result = await self.roles_ds.get_role_by_id(role_id)
        if result is None:
            return None
        return RoleInDb.model_validate(result)

    async def get_role_by_name(self, name: str) -> RoleInDb | None:
        result = await self.roles_ds.get_role_by_name(name)
        if result is None:
            return None
        return RoleInDb.model_validate(result)

    async def update_role_by_id(
        self, role_id: str, role: UpdateRole
    ) -> RoleInDb | None:
        updated_data = role.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.roles_ds.update_role_by_id(role_id, updated_data)
        if result is None:
            return None
        return RoleInDb.model_validate(result)

    async def delete_role_by_id(self, role_id: str) -> RoleInDb | None:
        result = await self.roles_ds.delete_role_by_id(role_id)
        if result is None:
            return None
        return RoleInDb.model_validate(result)
