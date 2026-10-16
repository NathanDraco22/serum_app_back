from fastapi import APIRouter
from repos.v1.app_settings import (
    AppSettingInDb,
    CreateAppSetting,
    UpdateAppSetting,
)
from responses.v1 import ListResponse

from .app_settings_controller import app_settings_controller

app_settings_router = APIRouter(tags=["app_settingsV1"])


@app_settings_router.post("")
async def create_app_setting(body: CreateAppSetting) -> AppSettingInDb:
    return await app_settings_controller.create_app_setting(body)


@app_settings_router.get("")
async def get_all_app_settings() -> ListResponse[AppSettingInDb]:
    return await app_settings_controller.get_all_app_settings()


@app_settings_router.get("/current")
async def get_current_app_settings() -> AppSettingInDb:
    return await app_settings_controller.get_current_app_settings()


@app_settings_router.get("/{app_setting_id}")
async def get_app_setting_by_id(app_setting_id: str) -> AppSettingInDb:
    return await app_settings_controller.get_app_setting_by_id(app_setting_id)


@app_settings_router.patch("/{app_setting_id}")
async def update_app_setting_by_id(
    app_setting_id: str, body: UpdateAppSetting
) -> AppSettingInDb:
    return await app_settings_controller.update_app_setting_by_id(app_setting_id, body)


@app_settings_router.delete("/{app_setting_id}")
async def delete_app_setting_by_id(app_setting_id: str) -> AppSettingInDb:
    return await app_settings_controller.delete_app_setting_by_id(app_setting_id)
