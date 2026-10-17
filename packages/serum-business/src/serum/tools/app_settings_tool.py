from serum.repos.v1.app_settings import (
    AppSettingInDb,
    AppSettingsDataSource,
    AppSettingsRepository,
)


class AppSettingsTool:
    _instance: "AppSettingsTool | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppSettingsTool, cls).__new__(cls)
        return cls._instance

    __current_app_settings: AppSettingInDb | None = None

    def __init__(self) -> None:
        pass

    async def get_current_app_settings(self) -> AppSettingInDb:
        if self.__current_app_settings is None:
            app_settings_repo = AppSettingsRepository(
                app_settings_ds=AppSettingsDataSource()
            )
            self.__current_app_settings = (
                await app_settings_repo.get_current_app_settings()
            )
        return self.__current_app_settings

    async def refresh_current_app_settings(self) -> None:
        app_settings_repo = AppSettingsRepository(
            app_settings_ds=AppSettingsDataSource()
        )
        self.__current_app_settings = (
            await app_settings_repo.get_current_app_settings()
        )
