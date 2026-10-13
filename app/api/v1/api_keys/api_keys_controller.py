from repos.v1.api_keys import (
    ApiKeyInDb,
    ApiKeysRepository,
    CreateApiKey,
    CreatedApiKeyResponse,
)
from responses.v1 import ListResponse


class ApiKeysController:
    def __init__(self, repo: ApiKeysRepository | None = None) -> None:
        self.repo = repo or ApiKeysRepository.get_instance()

    async def create_api_key(
        self, create_dto: CreateApiKey, created_by: str | None = None
    ) -> CreatedApiKeyResponse:
        return await self.repo.create_api_key(create_dto, created_by=created_by)

    async def get_all_api_keys(self) -> ListResponse[ApiKeyInDb]:
        api_keys = await self.repo.get_all_api_keys()
        return ListResponse(count=len(api_keys), data=api_keys)

    async def toggle_api_key_status(
        self, key_id: str, is_active: bool
    ) -> ApiKeyInDb | None:
        return await self.repo.toggle_api_key_status(key_id, is_active)

    async def delete_api_key(self, key_id: str) -> ApiKeyInDb | None:
        return await self.repo.delete_api_key(key_id)


api_keys_controller = ApiKeysController()
