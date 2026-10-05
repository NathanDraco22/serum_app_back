from fastapi import APIRouter

from repos.v1.auths import (
    CheckUserRequest,
    CheckUserResponse,
    LoginAttempt,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from repos.v1.core_settings import ServinStatusResponse

from .auths_controller import auths_controller

auths_router = APIRouter(tags=["authsV1"])


@auths_router.post("/login")
async def login(body: LoginAttempt) -> LoginResponse:
    return await auths_controller.login(body)


@auths_router.post("/refresh-token")
async def refresh_token(body: RefreshTokenRequest) -> RefreshTokenResponse:
    return await auths_controller.refresh_token(body)


@auths_router.post("/check-user")
async def check_user(body: CheckUserRequest) -> CheckUserResponse:
    return await auths_controller.check_user(body)


@auths_router.get("/servin-status")
async def get_servin_status() -> ServinStatusResponse:
    return await auths_controller.get_servin_status()
