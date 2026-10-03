import logging
import os
import time
from typing import Any

import jwt

logger = logging.getLogger(__name__)

SESSION_TOKEN_TTL_SEC = 8 * 60 * 60  # 8 horas en segundos
REFRESH_TOKEN_TTL_SEC = 30 * 24 * 60 * 60  # 30 días en segundos


class TokenManager:
    @staticmethod
    def _get_secret() -> str:
        return os.getenv("JWT_SECRET", "secretApp")

    @staticmethod
    def encode_token(payload: dict[str, Any]) -> str:
        secret = TokenManager._get_secret()
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        secret = TokenManager._get_secret()
        try:
            res = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
            )
            return res
        except jwt.PyJWTError as e:
            logger.warning("Token decode failed: %s", e)
            return None

    @staticmethod
    def verify_token_expiration(token: str) -> bool:
        payload = TokenManager.decode_token(token)
        if payload is None:
            return False

        expiration = payload.get("exp")
        if expiration is None:
            return False

        now = int(time.time())
        return int(expiration) >= now

    @staticmethod
    def create_session_token(
        user_id: str, username: str, role: str, access_level: int = 3
    ) -> str:
        now = int(time.time())
        return TokenManager.encode_token(
            {
                "exp": now + SESSION_TOKEN_TTL_SEC,
                "iat": now,
                "type": "session",
                "userId": user_id,
                "username": username,
                "role": role,
                "accessLevel": access_level,
            }
        )

    @staticmethod
    def create_refresh_token(
        user_id: str, username: str, role: str, access_level: int = 3
    ) -> str:
        now = int(time.time())
        return TokenManager.encode_token(
            {
                "exp": now + REFRESH_TOKEN_TTL_SEC,
                "iat": now,
                "type": "refresh",
                "userId": user_id,
                "username": username,
                "role": role,
                "accessLevel": access_level,
            }
        )
