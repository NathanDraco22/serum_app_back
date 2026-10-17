from serum.core.security import TokenManager
from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool

from .data.core_settings_datasource import CoreSettingsDataSource
from .models.core_setting_model import (
    CoreSettingInDb,
    CreateCoreSetting,
    DecodedCoreSetting,
    UpdateCoreSetting,
)


class CoreSettingsRepository:
    _instance: "CoreSettingsRepository | None" = None

    def __init__(self, core_settings_ds: CoreSettingsDataSource):
        self.core_settings_ds = core_settings_ds

    @classmethod
    def get_instance(cls) -> "CoreSettingsRepository":
        if cls._instance is None:
            cls._instance = CoreSettingsRepository(
                core_settings_ds=CoreSettingsDataSource()
            )
        return cls._instance

    async def create_core_setting(
        self, create_core_setting: CreateCoreSetting
    ) -> DecodedCoreSetting | None:
        decoded_data = TokenManager.super_token_verify(create_core_setting.token)

        if decoded_data is None:
            return None

        decoded_setting = DecodedCoreSetting.model_validate(decoded_data)

        new_settings = CoreSettingInDb(
            **create_core_setting.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.core_settings_ds.create_core_setting(new_settings.model_dump())

        return decoded_setting

    async def get_all_core_settings(self) -> list[CoreSettingInDb]:
        results = await self.core_settings_ds.get_all_core_settings()
        models = [CoreSettingInDb.model_validate(result) for result in results]
        return models

    async def get_core_setting_by_id(
        self, core_setting_id: str
    ) -> CoreSettingInDb | None:
        result = await self.core_settings_ds.get_core_setting_by_id(core_setting_id)
        if result is None:
            return None
        return CoreSettingInDb.model_validate(result)

    async def get_core_setting_by_nickname(
        self, nickname: str
    ) -> CoreSettingInDb | None:
        result = await self.core_settings_ds.get_core_setting_by_nickname(nickname)
        if result is None:
            return None
        return CoreSettingInDb.model_validate(result)

    async def update_core_setting_by_nickname(
        self, core_setting_nickname: str, core_setting: UpdateCoreSetting
    ) -> CoreSettingInDb | None:
        updated_data = core_setting.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.core_settings_ds.update_core_setting_by_nickname(
            core_setting_nickname, updated_data
        )
        if result is None:
            return None
        return CoreSettingInDb.model_validate(result)

    async def delete_core_setting_by_id(
        self, core_setting_id: str
    ) -> CoreSettingInDb | None:
        result = await self.core_settings_ds.delete_core_setting_by_id(core_setting_id)
        if result is None:
            return None
        return CoreSettingInDb.model_validate(result)
