from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

ph = PasswordHasher()


class SysPasswordHasher:
    @staticmethod
    def hash_password(password: str) -> str:
        hashed_password = ph.hash(password)

        return hashed_password

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        try:
            ph.verify(hashed_password, password)
            return True
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
