import logging
import os
from typing import Any

import jwt

from tools import TimeTools

logger = logging.getLogger(__name__)

SESSION_TOKEN_TTL_MS = 8 * 60 * 60 * 1000
REFRESH_TOKEN_TTL_MS = 30 * 24 * 60 * 60 * 1000


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
                options={"verify_exp": False},
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

        now = TimeTools.get_now_in_milliseconds()
        return int(expiration) >= int(now)

    @staticmethod
    def create_session_token(
        user_id: str, username: str, role: str
    ) -> str:
        now = TimeTools.get_now_in_milliseconds()
        return TokenManager.encode_token(
            {
                "exp": now + SESSION_TOKEN_TTL_MS,
                "iat": now,
                "type": "session",
                "userId": user_id,
                "username": username,
                "role": role,
            }
        )

    @staticmethod
    def create_refresh_token(
        user_id: str, username: str, role: str
    ) -> str:
        now = TimeTools.get_now_in_milliseconds()
        return TokenManager.encode_token(
            {
                "exp": now + REFRESH_TOKEN_TTL_MS,
                "iat": now,
                "type": "refresh",
                "userId": user_id,
                "username": username,
                "role": role,
            }
        )
