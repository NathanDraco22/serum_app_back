from core.default_values.create_default_branch import ORIGIN_BRANCH_ID
from core.security.password_hasher import SysPasswordHasher
from repos.v1.users.models.user_model import UserInDb
from services.mongo_collections.v1.users_collection import UsersCollection
from tools.time_tools import TimeTools

ROOT_USER_ID = "root"
ROOT_USERNAME = "Serum"
ROOT_PASSWORD_PLAIN = "SerumRoot"


async def create_root_user() -> UserInDb:
    hashed_password = SysPasswordHasher.hash_password(ROOT_PASSWORD_PLAIN)
    root_user = UserInDb(
        id=ROOT_USER_ID,
        username=ROOT_USERNAME,
        password=hashed_password,
        name="Administrador Serum",
        role="Admin",
        accessLevel=5,
        branches=[ORIGIN_BRANCH_ID],
        isActive=True,
        isInternal=True,
        createdAt=TimeTools.get_now_in_milliseconds(),
    )

    await UsersCollection.get_instance().create_user_if_absent(
        root_user.id,
        root_user.model_dump(),
    )
    await UsersCollection.get_instance().update_user_by_id(
        root_user.id,
        {"isInternal": True, "accessLevel": 5},
    )

    return root_user
