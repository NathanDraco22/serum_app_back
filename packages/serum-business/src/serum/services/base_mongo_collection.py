import os
from typing import Any, Type, TypeVar

from pymongo.asynchronous.collection import AsyncCollection

from serum.services.mongo_service import MongoService

T = TypeVar("T", bound="BaseMongoCollection")


class BaseMongoCollection:
    collection_name: str = ""
    _instances: dict[str, Any]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._instances = {}

    def __init__(self, nickname: str = "") -> None:
        self.nickname = nickname

    @property
    def _collection(self) -> AsyncCollection[dict[str, Any]]:
        from serum.serum_config import serumCtx

        target_db = (
            self.nickname
            or serumCtx.get().businessNickname
            or os.getenv("DB_NAME", "SerumDB")
        )
        return MongoService().get_collection(
            self.collection_name, database_name=target_db
        )

    @classmethod
    def get_instance(cls: Type[T], nickname: str | None = None) -> T:
        from serum.serum_config import serumCtx

        target_nickname = (
            nickname
            if nickname is not None
            else (serumCtx.get().businessNickname or os.getenv("DB_NAME", "SerumDB"))
        )
        if not hasattr(cls, "_instances"):
            cls._instances = {}

        if target_nickname not in cls._instances:
            cls._instances[target_nickname] = cls(nickname=target_nickname)
        return cls._instances[target_nickname]

