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
        return os.getenv("JWT_SECRET", "serum_super_secret_jwt_key_default_32bytes!!")

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
    def _find_service_public_key() -> Path | None:
        env_path = os.getenv("SERVICE_PUBLIC_KEY_PATH")
        if env_path and Path(env_path).exists():
            return Path(env_path)

        current = Path(__file__).resolve().parent
        for _ in range(8):
            for candidate in (
                current / "app" / "config" / "service_public_key.pem",
                current / "config" / "service_public_key.pem",
            ):
                if candidate.exists():
                    return candidate
            if current.parent == current:
                break
            current = current.parent

        for rel in (
            Path("app/config/service_public_key.pem"),
            Path("config/service_public_key.pem"),
        ):
            if rel.exists():
                return rel.resolve()

        return None

    @staticmethod
    def super_token_verify(token: str) -> dict[str, Any] | None:
        key_path = TokenManager._find_service_public_key()
        if key_path is None or not key_path.exists():
            logger.error("service_public_key.pem could not be located")
            return None

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
