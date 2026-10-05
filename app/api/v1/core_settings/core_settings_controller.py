from fastapi import HTTPException, status

from core.default_values import (
    ORIGIN_BRANCH_ID,
    create_default_branch,
    create_default_cash_register,
    create_default_roles,
)
from repos.v1.core_settings import (
    CoreSettingInDb,
    CoreSettingsRepository,
    CreateCoreSetting,
    DecodedCoreSetting,
    UpdateCoreSetting,
)
from repos.v1.users import CreateUser, UsersRepository


class CoreSettingsController:
    def __init__(
        self,
        core_settings_repo: CoreSettingsRepository,
        users_repo: UsersRepository,
    ) -> None:
        self.core_settings_repo = core_settings_repo
        self.users_repo = users_repo

    async def create_core_setting(
        self, body: CreateCoreSetting
    ) -> DecodedCoreSetting:
        settings = await self.get_all_core_settings()

        if len(settings) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CoreSetting already exists",
            )

        res = await self.core_settings_repo.create_core_setting(body)

        if res is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid core setting token or signature",
            )

        # 1. Crear / sincronizar sucursal con el nombre del establecimiento
        await create_default_branch(branch_name=res.name)

        # 2. Asegurar roles por defecto
        await create_default_roles()

        # 3. Asegurar caja registradora inicial
        await create_default_cash_register()

        # 4. Crear usuario administrador para el dueño si no existe
        existing_user = await self.users_repo.get_user_by_username(res.ownerName)
        if existing_user is None:
            origin_user = CreateUser(
                username=res.ownerName,
                password="12345",
                name=res.ownerName,
                role="Admin",
                accessLevel=5,
                branches=[ORIGIN_BRANCH_ID],
            )
            await self.users_repo.create_user(origin_user)

        return res

    async def get_all_core_settings(self) -> list[CoreSettingInDb]:
        core_settings = await self.core_settings_repo.get_all_core_settings()
        return core_settings

    async def get_core_setting_by_id(
        self, core_setting_id: str
    ) -> CoreSettingInDb:
        core_setting = await self.core_settings_repo.get_core_setting_by_id(
            core_setting_id
        )
        if core_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoreSetting not found",
            )
        return core_setting

    async def update_core_setting_by_nickname(
        self, core_setting_nickname: str, body: UpdateCoreSetting
    ) -> CoreSettingInDb:
        updated_core_setting = (
            await self.core_settings_repo.update_core_setting_by_nickname(
                core_setting_nickname, body
            )
        )
        if updated_core_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoreSetting not found",
            )
        return updated_core_setting

    async def delete_core_setting_by_id(
        self, core_setting_id: str
    ) -> CoreSettingInDb:
        deleted_core_setting = (
            await self.core_settings_repo.delete_core_setting_by_id(
                core_setting_id
            )
        )
        if deleted_core_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CoreSetting not found",
            )
        return deleted_core_setting


core_settings_controller = CoreSettingsController(
    core_settings_repo=CoreSettingsRepository.get_instance(),
    users_repo=UsersRepository.get_instance(),
)
