from typing import Any

from pydantic import BaseModel, model_validator


class LoginAttempt(BaseModel):
    username: str | None = None
    email: str | None = None
    phone: str | None = None
    password: str

    @model_validator(mode="after")
    def check_at_least_one_identifier(self) -> "LoginAttempt":
        if not any([self.username, self.email, self.phone]):
            raise ValueError(
                "At least one of username, email, or phone must be provided"
            )
        return self


class LoginResponse(BaseModel):
    user: dict[str, Any]
    token: str
    refreshToken: str


class RefreshTokenRequest(BaseModel):
    refreshToken: str


class RefreshTokenResponse(BaseModel):
    token: str
    refreshToken: str


class CheckUserRequest(BaseModel):
    token: str


class CheckUserResponse(BaseModel):
    status: str
