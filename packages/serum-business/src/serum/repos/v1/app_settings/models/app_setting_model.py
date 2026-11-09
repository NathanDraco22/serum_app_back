from typing import Literal

from pydantic import BaseModel

CurrencyCode = Literal["NIO", "USD", "HNL", "GTQ", "CRC", "COP", "MXN", "EUR"]


class BaseAppSetting(BaseModel):
    useCost: bool = False
    usePrice2: bool = False
    allowEditPrice: bool = False
    currency: CurrencyCode = "NIO"


class CreateAppSetting(BaseAppSetting):
    id: str = "Default"


class UpdateAppSetting(BaseModel):
    useCost: bool | None = None
    usePrice2: bool | None = None
    allowEditPrice: bool | None = None
    currency: CurrencyCode | None = None


class AppSettingInDb(BaseAppSetting):
    id: str = "Default"
    createdAt: int
    updatedAt: int | None = None
