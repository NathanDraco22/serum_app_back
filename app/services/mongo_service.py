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

    async def init_service(self):
        url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = AsyncMongoClient(url)
        await self.create_indexes()

    def get_collection(
        self,
        collection_name: str,
        database_name: DatabaseName = "SerumDB",
    ) -> AsyncCollection[dict[str, Any]]:
        db = self.client.get_database(database_name)
        return db.get_collection(collection_name)

    async def create_indexes(self):
        from services.mongo_collections.v1 import (
            DoctorsCollection,
            PatientsCollection,
            LabTestsCollection,
        )

        await DoctorsCollection.get_instance().create_indexes()
        await PatientsCollection.get_instance().create_indexes()
        await LabTestsCollection.get_instance().create_indexes()
