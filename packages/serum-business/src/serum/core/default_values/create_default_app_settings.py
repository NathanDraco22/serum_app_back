from serum.repos.v1.app_settings import (
    AppSettingsDataSource,
    AppSettingsRepository,
    CreateAppSetting,
)


async def create_default_app_settings() -> None:
    create_app_setting = CreateAppSetting()

    app_settings_repo = AppSettingsRepository(
        app_settings_ds=AppSettingsDataSource(),
    )

    await app_settings_repo.create_app_setting_if_absent(create_app_setting)
