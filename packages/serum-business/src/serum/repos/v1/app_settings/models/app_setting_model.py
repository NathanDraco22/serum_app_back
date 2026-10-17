from pydantic import BaseModel


class BaseAppSetting(BaseModel):
    useCost: bool = False
    usePrice2: bool = False
    allowEditPrice: bool = False


class CreateAppSetting(BaseAppSetting):
    id: str = "Default"


class UpdateAppSetting(BaseModel):
    useCost: bool | None = None
    usePrice2: bool | None = None
    allowEditPrice: bool | None = None


class AppSettingInDb(BaseAppSetting):
    id: str = "Default"
    createdAt: int
    updatedAt: int | None = None
