from pydantic import BaseModel


class BaseApiKey(BaseModel):
    name: str
    serviceType: str = "power_bi"  # "power_bi", "ecommerce", "custom", "external_lis"
    scopes: list[str] = ["bi:read"]
    branchId: str | None = None


class CreateApiKey(BaseApiKey):
    pass


class ApiKeyInDb(BaseApiKey):
    id: str
    key: str  # srm_live_...
    maskedKey: str  # srm_live_k9X2...4hJ1
    isActive: bool = True
    createdAt: int
    updatedAt: int | None = None
    lastUsedAt: int | None = None
    createdBy: str | None = None
    isDeleted: bool = False


class CreatedApiKeyResponse(ApiKeyInDb):
    rawKey: str
