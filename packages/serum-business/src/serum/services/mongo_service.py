import os
from typing import Any, Literal

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

DatabaseName = Literal["SerumDB"]


class MongoService:
    client: AsyncMongoClient
    _instance: "MongoService|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoService, cls).__new__(cls)
        return cls._instance

    client: AsyncMongoClient[dict[str, Any]]

    async def init_client(self):
        url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = AsyncMongoClient(url)

    async def init_service(self):
        await self.init_client()
        await self.create_indexes()

    def get_collection(
        self,
        collection_name: str,
        database_name: str | None = None,
    ) -> AsyncCollection[dict[str, Any]]:
        from serum.serum_config import serumCtx

        ctx = serumCtx.get()
        if database_name:
            current_db_name = database_name
        elif ctx.businessNickname:
            current_db_name = ctx.businessNickname
        else:
            current_db_name = os.getenv("DB_NAME", "SerumDB")

        db = self.client.get_database(current_db_name)
        return db.get_collection(collection_name)

    async def create_tenant_indexes(self, nickname: str | None = None):
        from serum.core.reports.database_indexes import ensure_reports_indexes
        from serum.services.mongo_collections.v1 import (
            ApiKeysCollection,
            CountersCollection,
            DoctorsCollection,
            LabTestAccountsCollection,
            LabTestsCollection,
            PatientsCollection,
        )

        await CountersCollection.get_instance(nickname).create_indexes()
        await DoctorsCollection.get_instance(nickname).create_indexes()
        await PatientsCollection.get_instance(nickname).create_indexes()
        await LabTestsCollection.get_instance(nickname).create_indexes()
        await LabTestAccountsCollection.get_instance(nickname).create_indexes()
        await ApiKeysCollection.get_instance(nickname).create_indexes()
        await ensure_reports_indexes(nickname=nickname)

    async def create_indexes(self):
        await self.create_tenant_indexes(None)

