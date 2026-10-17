import secrets

from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool

from .data.api_keys_data_source import ApiKeysDataSource
from .models.api_key_model import ApiKeyInDb, CreateApiKey, CreatedApiKeyResponse


class ApiKeysRepository:
    _instance: "ApiKeysRepository | None" = None

    def __init__(self, api_keys_ds: ApiKeysDataSource) -> None:
        self.api_keys_ds = api_keys_ds

    @classmethod
    def get_instance(cls) -> "ApiKeysRepository":
        if cls._instance is None:
            cls._instance = ApiKeysRepository(api_keys_ds=ApiKeysDataSource())
        return cls._instance

    def _generate_token(self) -> str:
        random_str = secrets.token_urlsafe(32)
        return f"srm_live_{random_str}"

    def _mask_token(self, token: str) -> str:
        if len(token) <= 16:
            return token
        return f"{token[:12]}...{token[-4:]}"

    async def create_api_key(
        self, create_dto: CreateApiKey, created_by: str | None = None
    ) -> CreatedApiKeyResponse:
        raw_key = self._generate_token()
        masked_key = self._mask_token(raw_key)
        now = TimeTools.get_now_in_milliseconds()

        api_key_in_db = ApiKeyInDb(
            id=f"key_{UuidTool.generate_uuid()[:12]}",
            key=raw_key,
            maskedKey=masked_key,
            isActive=True,
            createdAt=now,
            updatedAt=None,
            lastUsedAt=None,
            createdBy=created_by,
            isDeleted=False,
            **create_dto.model_dump(),
        )

        await self.api_keys_ds.create_api_key(api_key_in_db.model_dump())

        return CreatedApiKeyResponse(
            **api_key_in_db.model_dump(),
            rawKey=raw_key,
        )

    async def get_all_api_keys(self) -> list[ApiKeyInDb]:
        results = await self.api_keys_ds.get_all_api_keys()
        return [ApiKeyInDb.model_validate(r) for r in results]

    async def get_api_key_by_id(self, key_id: str) -> ApiKeyInDb | None:
        result = await self.api_keys_ds.get_api_key_by_id(key_id)
        if result is None:
            return None
        return ApiKeyInDb.model_validate(result)

    async def verify_and_get_key(self, raw_key_value: str) -> ApiKeyInDb | None:
        result = await self.api_keys_ds.get_api_key_by_value(raw_key_value)
        if result is None:
            return None

        api_key = ApiKeyInDb.model_validate(result)
        if not api_key.isActive or api_key.isDeleted:
            return None

        now = TimeTools.get_now_in_milliseconds()
        await self.api_keys_ds.update_last_used_at(api_key.id, now)
        api_key.lastUsedAt = now

        return api_key

    async def toggle_api_key_status(
        self, key_id: str, is_active: bool
    ) -> ApiKeyInDb | None:
        now = TimeTools.get_now_in_milliseconds()
        result = await self.api_keys_ds.toggle_api_key_status(key_id, is_active, now)
        if result is None:
            return None
        return ApiKeyInDb.model_validate(result)

    async def delete_api_key(self, key_id: str) -> ApiKeyInDb | None:
        now = TimeTools.get_now_in_milliseconds()
        result = await self.api_keys_ds.delete_api_key_by_id(key_id, now)
        if result is None:
            return None
        return ApiKeyInDb.model_validate(result)
