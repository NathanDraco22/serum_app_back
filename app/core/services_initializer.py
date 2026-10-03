from core.default_values import (
    create_default_branch,
    create_default_cash_register,
    create_default_roles,
    create_root_user,
)
from services.mongo_service import MongoService


async def init_services() -> None:
    await MongoService().init_service()
    await create_default_branch()
    await create_default_cash_register()
    await create_default_roles()
    await create_root_user()
