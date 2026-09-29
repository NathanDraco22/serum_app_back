from core.default_values import create_default_branch, create_root_user
from services.mongo_service import MongoService


async def init_services() -> None:
    await MongoService().init_service()
    await create_default_branch()
    await create_root_user()
