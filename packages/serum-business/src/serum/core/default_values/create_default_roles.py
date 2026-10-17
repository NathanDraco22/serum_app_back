from serum.repos.v1.roles.models.role_model import RoleInDb
from serum.services.mongo_collections.v1.roles_collection import RolesCollection
from serum.tools.time_tools import TimeTools

ROLE_ADMIN_ID = "role_admin"
ROLE_ADMIN_NAME = "Admin"

ROLE_OPERATOR_ID = "role_operator"
ROLE_OPERATOR_NAME = "Operador"


async def create_default_roles() -> None:
    now = TimeTools.get_now_in_milliseconds()
    roles_collection = RolesCollection.get_instance()

    admin_role = RoleInDb(
        id=ROLE_ADMIN_ID,
        name=ROLE_ADMIN_NAME,
        accessLevel=5,
        description="Administrador con acceso total y configuración del sistema",
        createdAt=now,
        isDeleted=False,
    )
    await roles_collection.create_role_if_absent(
        admin_role.id,
        admin_role.model_dump(),
    )

    operator_role = RoleInDb(
        id=ROLE_OPERATOR_ID,
        name=ROLE_OPERATOR_NAME,
        accessLevel=3,
        description="Operador con acceso estándar a laboratorio, pacientes, órdenes y caja",
        createdAt=now,
        isDeleted=False,
    )
    await roles_collection.create_role_if_absent(
        operator_role.id,
        operator_role.model_dump(),
    )
