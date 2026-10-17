import contextvars
from dataclasses import dataclass


class SerumConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SerumConfig, cls).__new__(cls)
        return cls._instance


@dataclass
class SerumContext:
    businessNickname: str = ""
    branchId: str = ""


serumCtx = contextvars.ContextVar("serumCtx", default=SerumContext())
