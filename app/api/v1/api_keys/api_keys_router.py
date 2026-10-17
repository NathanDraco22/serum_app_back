from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app_middleware.depends.auth_middleware import auth_middleware
from serum.repos.v1.api_keys import (
    ApiKeyInDb,
    CreateApiKey,
    CreatedApiKeyResponse,
)
from responses.v1 import ListResponse

from .api_keys_controller import api_keys_controller

api_keys_router = APIRouter(
    tags=["apiKeysV1"],
    dependencies=[Depends(auth_middleware)],
)


class ToggleApiKeyRequest(BaseModel):
    isActive: bool


@api_keys_router.get("")
async def get_all_api_keys() -> ListResponse[ApiKeyInDb]:
    return await api_keys_controller.get_all_api_keys()


@api_keys_router.post(
    "",
    response_model=CreatedApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    create_dto: CreateApiKey, req: Request
) -> CreatedApiKeyResponse:
    created_by = getattr(req.state, "user_id", None)
    return await api_keys_controller.create_api_key(
        create_dto, created_by=created_by
    )


@api_keys_router.patch("/{key_id}/toggle", response_model=ApiKeyInDb)
async def toggle_api_key_status(
    key_id: str, body: ToggleApiKeyRequest
) -> ApiKeyInDb:
    result = await api_keys_controller.toggle_api_key_status(
        key_id, body.isActive
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Llave de API no encontrada",
        )
    return result


@api_keys_router.delete("/{key_id}", response_model=ApiKeyInDb)
async def delete_api_key(key_id: str) -> ApiKeyInDb:
    result = await api_keys_controller.delete_api_key(key_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Llave de API no encontrada",
        )
    return result
