import logging
from serum.core.default_values import (
    ORIGIN_BRANCH_ID,
    create_default_app_settings,
    create_default_branch,
    create_default_cash_register,
    create_default_lab_tests,
    create_default_roles,
    create_root_user,
)
from serum.repos.v1.users import CreateUser, UsersRepository
from serum.serum_config import SerumContext, serumCtx
from serum.services.mongo_service import MongoService

logger = logging.getLogger(__name__)


async def provision_tenant(
    nickname: str,
    establishment_name: str | None = None,
    owner_name: str | None = None,
    owner_password: str = "12345",
) -> None:
    """
    Aprovisiona de forma atómica una nueva base de datos para un laboratorio (tenant):
    1. Establece el contexto aislado del tenant.
    2. Crea todos los índices en todas las colecciones para esa base de datos.
    3. Inicializa la sucursal principal con el nombre del establecimiento.
    4. Inicializa los roles del sistema.
    5. Inicializa la caja registradora principal.
    6. Inicializa las configuraciones de la aplicación (AppSettings).
    7. Inicializa el catálogo base de pruebas de laboratorio.
    8. Crea el usuario Root y el usuario Administrador del propietario.
    """
    token = serumCtx.set(SerumContext(businessNickname=nickname))
    try:
        # 1. Crear sucursal de origen
        branch_name = establishment_name or "Origen"
        await create_default_branch(branch_name=branch_name)

        # 2. Roles del sistema
        await create_default_roles()

        # 3. Usuario Root del sistema
        await create_root_user()

        # 4. Usuario Administrador del propietario (si se especificó)
        if owner_name:
            users_repo = UsersRepository.get_instance()
            existing_user = await users_repo.get_user_by_username(owner_name)
            if existing_user is None:
                owner_user = CreateUser(
                    username=owner_name,
                    password=owner_password,
                    name=owner_name,
                    role="Admin",
                    accessLevel=5,
                    branches=[ORIGIN_BRANCH_ID],
                )
                await users_repo.create_user(owner_user)

        # 5. Caja registradora principal
        await create_default_cash_register()

        # 6. Configuraciones de la aplicación
        await create_default_app_settings()

        # 7. Crear todos los índices de colecciones y reportes en paralelo
        await MongoService().create_tenant_indexes(nickname=nickname)

        # 8. Catálogo base de pruebas clínicas (en lote masivo)
        await create_default_lab_tests()
    finally:
        serumCtx.reset(token)
