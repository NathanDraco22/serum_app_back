from fastapi import BackgroundTasks, HTTPException, status

from serum.core.tenant import provision_tenant
from serum.repos.v1.core_settings import (
    CoreSettingInDb,
    CoreSettingsRepository,
    CreateCoreSetting,
    DecodedCoreSetting,
    UpdateCoreSetting,
)
from serum.repos.v1.users import UsersRepository


class CoreSettingsController:
    def __init__(
        self,
        core_settings_repo: CoreSettingsRepository,
        users_repo: UsersRepository,
    ) -> None:
        self.core_settings_repo = core_settings_repo
        self.users_repo = users_repo

    async def create_core_setting(
        self,
        body: CreateCoreSetting,
        background_tasks: BackgroundTasks | None = None,
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

        # Aprovisionar en segundo plano para responder de inmediato (< 50ms) y evitar timeouts del cliente (HTTP 499)
        if background_tasks is not None:
            background_tasks.add_task(
                provision_tenant,
                nickname=res.nickname,
                establishment_name=res.name,
                owner_name=res.ownerName,
            )
        else:
            await provision_tenant(
                nickname=res.nickname,
                establishment_name=res.name,
                owner_name=res.ownerName,
            )

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
