from services.mongo_service import MongoService


async def init_services() -> None:
    await MongoService().init_service()
