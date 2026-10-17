from fastapi import HTTPException, status
from serum.repos.v1.app_settings import (
    AppSettingInDb,
    AppSettingsRepository,
    CreateAppSetting,
    UpdateAppSetting,
)
from responses.v1 import ListResponse
from serum.tools.app_settings_tool import AppSettingsTool


class AppSettingsController:
    def __init__(self, app_settings_repo: AppSettingsRepository) -> None:
        self.app_settings_repo = app_settings_repo

    async def create_app_setting(self, body: CreateAppSetting) -> AppSettingInDb:
        return await self.app_settings_repo.create_app_setting(body)

    async def get_all_app_settings(self) -> ListResponse[AppSettingInDb]:
        app_settings = await self.app_settings_repo.get_all_app_settings()
        return ListResponse(
            count=len(app_settings),
            data=app_settings,
        )

    async def get_current_app_settings(self) -> AppSettingInDb:
        return await AppSettingsTool().get_current_app_settings()

    async def get_app_setting_by_id(self, app_setting_id: str) -> AppSettingInDb:
        app_setting = await self.app_settings_repo.get_app_setting_by_id(app_setting_id)
        if app_setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AppSetting not found",
            )
        return app_setting

    async def update_app_setting_by_id(
        self, app_setting_id: str, body: UpdateAppSetting
    ) -> AppSettingInDb:
        updated = await self.app_settings_repo.update_app_setting_by_id(
            app_setting_id, body
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AppSetting not found",
            )

        await AppSettingsTool().refresh_current_app_settings()
        return updated

    async def delete_app_setting_by_id(self, app_setting_id: str) -> AppSettingInDb:
        deleted = await self.app_settings_repo.delete_app_setting_by_id(app_setting_id)
        if deleted is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AppSetting not found",
            )
        await AppSettingsTool().refresh_current_app_settings()
        return deleted


app_settings_controller = AppSettingsController(
    app_settings_repo=AppSettingsRepository.get_instance(),
)
