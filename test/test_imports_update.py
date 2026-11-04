import time
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
import pytest

from serum.core.default_values import (
    ORIGIN_BRANCH_ID,
    create_default_branch,
    create_default_lab_tests,
)
from serum.core.security import TokenManager
from serum.repos.v1.lab_test_accounts import (
    LabTestAccountsRepository,
    UpdateLabTestAccountCommercial,
)
from serum.repos.v1.lab_tests import LabTestsRepository, UpdateLabTest
from serum.repos.v1.users import CreateUser, UsersRepository
from serum.serum_config import SerumContext, serumCtx
from serum.services_initializer import init_services
from main import app


@pytest.mark.asyncio
async def test_update_catalog_authorization_and_price_preservation():
    load_dotenv("app/.env")
    await init_services()

    transport = ASGITransport(app=app)
    tenant_nickname = f"tenant_update_{int(time.time())}"
    tenant_headers = {
        "x-tenant-nickname": tenant_nickname,
        "x-branch": ORIGIN_BRANCH_ID,
    }

    ctx_token = serumCtx.set(
        SerumContext(businessNickname=tenant_nickname, branchId=ORIGIN_BRANCH_ID)
    )
    try:
        users_repo = UsersRepository.get_instance()
        lab_tests_repo = LabTestsRepository.get_instance()
        accounts_repo = LabTestAccountsRepository.get_instance()

        # Asegurar branch de origen
        await create_default_branch()

        # Crear usuarios con diferentes niveles
        operator_user = await users_repo.create_user(
            CreateUser(
                username=f"op_{int(time.time())}",
                name="Operador",
                password="OperatorPassword123",
                role="operator",
                branches=[ORIGIN_BRANCH_ID],
                accessLevel=2,
            )
        )
        admin_user = await users_repo.create_user(
            CreateUser(
                username=f"adm_{int(time.time())}",
                name="Admin",
                password="AdminPassword123",
                role="admin",
                branches=[ORIGIN_BRANCH_ID],
                accessLevel=5,
            )
        )

        # Cargar catálogo inicial por defecto
        await create_default_lab_tests()

        # Simular que el usuario configuró precios personalizados para "GLU"
        glu_test = (await lab_tests_repo.get_all_lab_tests())
        glu = next((t for t in glu_test if t.code == "GLU"), None)
        assert glu is not None, "El test GLU debe existir en el catálogo maestro."

        custom_sale_price = 99900  # $999.00
        custom_sale_price2 = 88800  # $888.00
        custom_cost_price = 33300   # $333.00

        await lab_tests_repo.update_lab_test_by_id(
            glu.id,
            UpdateLabTest(
                salePrice=custom_sale_price,
                salePrice2=custom_sale_price2,
                costPrice=custom_cost_price,
                subclassification="Subclasificación Antigua",
            ),
        )
        await accounts_repo.update_commercial_by_branch_and_test(
            branchId=ORIGIN_BRANCH_ID,
            labTestId=glu.id,
            update_model=UpdateLabTestAccountCommercial(
                salePrice=custom_sale_price,
                salePrice2=custom_sale_price2,
                costPrice=custom_cost_price,
            ),
        )

    finally:
        serumCtx.reset(ctx_token)

    operator_token = TokenManager.create_session_token(
        user_id=operator_user.id,
        username=operator_user.username,
        role=operator_user.role,
        access_level=operator_user.accessLevel,
    )
    admin_token = TokenManager.create_session_token(
        user_id=admin_user.id,
        username=admin_user.username,
        role=admin_user.role,
        access_level=admin_user.accessLevel,
    )

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Petición sin autenticación -> 401
        res_no_auth = await client.post(
            "/api/v1/imports/update-catalog",
            headers=tenant_headers,
            json={"overridePrice": False, "updateLabTest": True},
        )
        assert res_no_auth.status_code == 401

        # 2. Petición con operador (accessLevel=2) -> 403
        res_forbidden = await client.post(
            "/api/v1/imports/update-catalog",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {operator_token}",
            },
            json={"overridePrice": False, "updateLabTest": True},
        )
        assert res_forbidden.status_code == 403

        # 3. Petición con updateLabTest=False -> 200 sin cambios
        res_skip = await client.post(
            "/api/v1/imports/update-catalog",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {admin_token}",
            },
            json={"overridePrice": False, "updateLabTest": False},
        )
        assert res_skip.status_code == 200
        skip_data = res_skip.json()
        assert skip_data["success"] is True
        assert skip_data["totalProcessed"] == 0

        # 4. Actualización con overridePrice=False (PRESERVAR PRECIOS DEL USUARIO)
        res_update_preserve = await client.post(
            "/api/v1/imports/update-catalog",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {admin_token}",
            },
            json={"overridePrice": False, "updateLabTest": True},
        )
        assert res_update_preserve.status_code == 200
        preserve_data = res_update_preserve.json()
        assert preserve_data["success"] is True
        assert preserve_data["updatedTestsCount"] > 0
        assert preserve_data["skippedPricesCount"] > 0

        # Verificar que GLU actualizó sus metadatos pero MANTUVO sus precios intactos
        ctx_token = serumCtx.set(
            SerumContext(businessNickname=tenant_nickname, branchId=ORIGIN_BRANCH_ID)
        )
        try:
            glu_after = await lab_tests_repo.get_lab_test_by_id(glu.id)
            assert glu_after is not None
            # Precios intactos
            assert glu_after.salePrice == custom_sale_price
            assert glu_after.salePrice2 == custom_sale_price2
            assert glu_after.costPrice == custom_cost_price
            # Metadatos actualizados desde el static
            assert glu_after.subclassification != "Subclasificación Antigua"

            account_after = await accounts_repo.get_by_branch_and_test(
                ORIGIN_BRANCH_ID, glu.id
            )
            assert account_after is not None
            assert account_after.commercial.salePrice == custom_sale_price
        finally:
            serumCtx.reset(ctx_token)

        # 5. Actualización con overridePrice=True vía Alias /sync-catalog (SOBREESCRIBIR PRECIOS)
        res_update_override = await client.post(
            "/api/v1/imports/sync-catalog",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {admin_token}",
            },
            json={"overridePrice": True, "updateLabTest": True},
        )
        assert res_update_override.status_code == 200
        override_data = res_update_override.json()
        assert override_data["success"] is True
        assert override_data["updatedAccountsCount"] > 0

        # Verificar que GLU ahora sí actualizó sus precios al valor oficial del master JSON
        ctx_token = serumCtx.set(
            SerumContext(businessNickname=tenant_nickname, branchId=ORIGIN_BRANCH_ID)
        )
        try:
            glu_overridden = await lab_tests_repo.get_lab_test_by_id(glu.id)
            assert glu_overridden is not None
            # El precio ya no debe ser el custom del usuario
            assert glu_overridden.salePrice != custom_sale_price
            # Debe coincidir con el del catálogo maestro
            account_overridden = await accounts_repo.get_by_branch_and_test(
                ORIGIN_BRANCH_ID, glu.id
            )
            assert account_overridden is not None
            assert account_overridden.commercial.salePrice == glu_overridden.salePrice

            # 6. Validar que los packs resolvieron correctamente sus childTestIds
            ego_pack = next((t for t in await lab_tests_repo.get_all_lab_tests() if t.code == "EGO"), None)
            assert ego_pack is not None
            assert ego_pack.isPack is True
            assert len(ego_pack.childTestIds) == 24
        finally:
            serumCtx.reset(ctx_token)

        # 7. Validar payload con snake_case (AliasChoices: override_price y update_lab_test)
        res_snake = await client.post(
            "/api/v1/imports/update-catalog",
            headers={
                **tenant_headers,
                "Authorization": f"Bearer {admin_token}",
            },
            json={"override_price": False, "update_lab_test": True},
        )
        assert res_snake.status_code == 200
        assert res_snake.json()["success"] is True
