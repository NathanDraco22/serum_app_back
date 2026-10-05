import logging
import os
from pathlib import Path
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

    @staticmethod
    def super_token_verify(token: str) -> dict[str, Any] | None:
        key_path = (
            Path(__file__).resolve().parent.parent.parent
            / "config"
            / "service_public_key.pem"
        )
        if not key_path.exists():
            key_path = Path("app/config/service_public_key.pem")
        if not key_path.exists():
            key_path = Path("config/service_public_key.pem")

        try:
            with open(key_path, "rb") as f:
                public_key_bytes = f.read()
            res = jwt.decode(token, public_key_bytes, algorithms=["EdDSA"])
            return res
        except jwt.PyJWTError as e:
            logger.warning("Super token verify failed: %s", e)
            return None
        except Exception as e:
            logger.error("Error verifying super token: %s", e)
            return None
