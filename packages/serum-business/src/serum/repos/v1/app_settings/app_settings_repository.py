from serum.tools.time_tools import TimeTools
from .data.app_settings_data_source import AppSettingsDataSource
from .models.app_setting_model import (
    AppSettingInDb,
    CreateAppSetting,
    UpdateAppSetting,
)


class AppSettingsRepository:
    _instance: "AppSettingsRepository | None" = None

    def __init__(self, app_settings_ds: AppSettingsDataSource):
        self.app_settings_ds = app_settings_ds

    @classmethod
    def get_instance(cls) -> "AppSettingsRepository":
        if cls._instance is None:
            cls._instance = AppSettingsRepository(
                app_settings_ds=AppSettingsDataSource()
            )
        return cls._instance

    async def create_app_setting(
        self, create_app_setting: CreateAppSetting
    ) -> AppSettingInDb:
        new_app_setting = AppSettingInDb(
            **create_app_setting.model_dump(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )
        await self.app_settings_ds.create_app_setting(new_app_setting.model_dump())
        return new_app_setting

    async def create_app_setting_if_absent(
        self, create_app_setting: CreateAppSetting
    ) -> AppSettingInDb:
        new_app_setting = AppSettingInDb(
            **create_app_setting.model_dump(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )
        await self.app_settings_ds.create_app_setting_if_absent(
            new_app_setting.model_dump()
        )
        return new_app_setting

    async def get_all_app_settings(self) -> list[AppSettingInDb]:
        results = await self.app_settings_ds.get_all_app_settings()
        return [AppSettingInDb.model_validate(result) for result in results]

    async def get_app_setting_by_id(
        self, app_setting_id: str
    ) -> AppSettingInDb | None:
        result = await self.app_settings_ds.get_app_setting_by_id(app_setting_id)
        if result is None:
            return None
        return AppSettingInDb.model_validate(result)

    async def get_current_app_settings(self) -> AppSettingInDb:
        setting = await self.get_app_setting_by_id("Default")
        if setting is not None:
            return setting

        all_settings = await self.get_all_app_settings()
        if len(all_settings) > 0:
            return all_settings[0]

        return await self.create_app_setting_if_absent(CreateAppSetting())

    async def update_app_setting_by_id(
        self, app_setting_id: str, app_setting: UpdateAppSetting
    ) -> AppSettingInDb | None:
        update_data = app_setting.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_app_setting_by_id(app_setting_id)

        update_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.app_settings_ds.update_app_setting_by_id(
            app_setting_id, update_data
        )

        if result is None:
            return None

        return AppSettingInDb.model_validate(result)

    async def delete_app_setting_by_id(
        self, app_setting_id: str
    ) -> AppSettingInDb | None:
        result = await self.app_settings_ds.delete_app_setting_by_id(app_setting_id)
        if result is None:
            return None
        return AppSettingInDb.model_validate(result)
