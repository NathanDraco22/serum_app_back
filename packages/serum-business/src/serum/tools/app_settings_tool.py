import os

from serum.repos.v1.app_settings import (
    AppSettingInDb,
    AppSettingsDataSource,
    AppSettingsRepository,
)
from serum.serum_config import serumCtx



class AppSettingsTool:
    _instance: "AppSettingsTool | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppSettingsTool, cls).__new__(cls)
        return cls._instance

    __current_app_settings: dict[str, AppSettingInDb] = {}

    def __init__(self) -> None:
        pass

    async def get_current_app_settings(
        self, nickname: str | None = None
    ) -> AppSettingInDb:
        key = nickname or serumCtx.get().businessNickname or os.getenv("DB_NAME", "SerumDB")
        if key not in self.__current_app_settings:
            app_settings_repo = AppSettingsRepository(
                app_settings_ds=AppSettingsDataSource()
            )
            self.__current_app_settings[key] = (
                await app_settings_repo.get_current_app_settings()
            )
        return self.__current_app_settings[key]

    async def refresh_current_app_settings(
        self, nickname: str | None = None
    ) -> None:
        key = nickname or serumCtx.get().businessNickname or os.getenv("DB_NAME", "SerumDB")
        app_settings_repo = AppSettingsRepository(
            app_settings_ds=AppSettingsDataSource()
        )
        self.__current_app_settings[key] = (
            await app_settings_repo.get_current_app_settings()
        )

