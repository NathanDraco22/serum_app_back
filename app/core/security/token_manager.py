import os

import jwt

from tools import TimeTools


class TokenManager:
    @staticmethod
    def encode_token(payload) -> str:
        secret = os.getenv("JWT_SECRET", "secretApp")
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def verify_token_expiration(token: str) -> bool:
        payload = jwt.decode(token, verify=False)

        expiration = payload.get("exp")
        if expiration is None:
            return False

        if int(expiration) < int(TimeTools.get_now_in_milliseconds()):
            return False

        return True

    @staticmethod
    def decode_token(token) -> dict | None:
        secret = os.getenv("JWT_SECRET", "secretApp")
        try:
            res = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            return res
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def super_token_verify(token: str) -> dict | None:
        with open("config/service_public_key.pem", "rb") as f:
            public_key_bytes = f.read()

        try:
            res = jwt.decode(token, public_key_bytes, algorithms=["EdDSA"])
            return res
        except Exception as e:
            print(e)
            return None
