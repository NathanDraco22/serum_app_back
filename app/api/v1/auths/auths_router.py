from fastapi import APIRouter

from repos.v1.auths import (
    CheckUserRequest,
    CheckUserResponse,
    LoginAttempt,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)

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
