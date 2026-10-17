from fastapi import HTTPException, status

from serum.core.security import SysPasswordHasher, TokenManager
from serum.repos.v1.auths import (
    CheckUserRequest,
    CheckUserResponse,
    LoginAttempt,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from serum.repos.v1.core_settings import (
    CoreSettingsRepository,
    DecodedCoreSetting,
    ServinStatusResponse,
)
from serum.repos.v1.users import UsersRepository


class AuthController:
    def __init__(
        self,
        users_repo: UsersRepository,
        core_settings_repo: CoreSettingsRepository,
    ) -> None:
        self.users_repo = users_repo
        self.core_settings_repo = core_settings_repo

    async def login(self, body: LoginAttempt) -> LoginResponse:
        user = None

        if body.username:
            user = await self.users_repo.get_user_by_username(body.username)
        if user is None and body.email:
            user = await self.users_repo.get_user_by_email(body.email)
        if user is None and body.phone:
            user = await self.users_repo.get_user_by_phone(body.phone)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not SysPasswordHasher.verify_password(body.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        session_token = TokenManager.create_session_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            access_level=user.accessLevel,
        )

        refresh_token = TokenManager.create_refresh_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            access_level=user.accessLevel,
        )

        user_data = user.model_dump(exclude={"password"})

        return LoginResponse(
            user=user_data,
            token=session_token,
            refreshToken=refresh_token,
        )

    async def refresh_token(
        self, body: RefreshTokenRequest
    ) -> RefreshTokenResponse:
        payload = TokenManager.decode_token(body.refreshToken)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        if not TokenManager.verify_token_expiration(body.refreshToken):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )

        user_id = payload["userId"]
        username = payload["username"]
        role = payload["role"]

        existing_user = await self.users_repo.get_user_by_id(user_id)
        if existing_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )

        session_token = TokenManager.create_session_token(
            user_id=user_id,
            username=username,
            role=role,
            access_level=existing_user.accessLevel,
        )

        new_refresh_token = TokenManager.create_refresh_token(
            user_id=user_id,
            username=username,
            role=role,
            access_level=existing_user.accessLevel,
        )

        return RefreshTokenResponse(
            token=session_token,
            refreshToken=new_refresh_token,
        )

    async def check_user(
        self, body: CheckUserRequest
    ) -> CheckUserResponse:
        payload = TokenManager.decode_token(body.token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        if not TokenManager.verify_token_expiration(body.token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )

        user = await self.users_repo.get_user_by_id(payload["userId"])
        if user is None or user.isDeleted:
            return CheckUserResponse(status="deleted")

        if not user.isActive:
            return CheckUserResponse(status="unactive")

        return CheckUserResponse(status="active")

    async def get_servin_status(self) -> ServinStatusResponse:
        core_settings = await self.core_settings_repo.get_all_core_settings()

        if len(core_settings) < 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Servin not configured",
            )

        current_core_setting = core_settings[0]
        decoded_settings = TokenManager.super_token_verify(
            current_core_setting.token
        )

        if decoded_settings is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid Servin token",
            )

        settings = DecodedCoreSetting.model_validate(decoded_settings)

        return ServinStatusResponse(
            nickname=settings.nickname,
            isActive=settings.isActive,
            isMultiBranch=settings.isMultiBranch,
            isUsingExpirationDate=settings.isUsingExpirationDate,
        )


auths_controller = AuthController(
    users_repo=UsersRepository.get_instance(),
    core_settings_repo=CoreSettingsRepository.get_instance(),
)
