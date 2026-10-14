import pytest
from dotenv import load_dotenv

from core.default_values.create_default_branch import ORIGIN_BRANCH_ID
from core.default_values.create_default_lab_tests import create_default_lab_tests
from core.services_initializer import init_services
from repos.v1.lab_test_accounts import LabTestAccountsRepository
from repos.v1.lab_tests import LabTestsRepository


@pytest.mark.asyncio
async def test_create_default_lab_tests_from_static_and_idempotency():
    load_dotenv("app/.env")

    # 1. Iniciar servicios del sistema
    await init_services()

    lab_tests_repo = LabTestsRepository.get_instance()
    accounts_repo = LabTestAccountsRepository.get_instance()

    # 2. Consultar todos los tests cargados
    all_tests = await lab_tests_repo.get_all_lab_tests()
    tests_by_code = {t.code: t for t in all_tests if t.code}

    expected_codes = [
        "GLU", "CREA", "TGO", "TGP", "GGT",
        "BIL-T", "BIL-D", "BIL-I", "ALP", "PROT-T",
        "TSH", "T4L", "T3", "INS", "PERF-HEP"
    ]

    for code in expected_codes:
        assert code in tests_by_code, f"El test con código '{code}' debería haberse cargado desde static."

    # 3. Validar el Pack y la resolución de childTestIds
    pack = tests_by_code["PERF-HEP"]
    assert pack.isPack is True
    assert len(pack.childTestIds) == 8

    expected_child_codes = [
        "TGO", "TGP", "GGT", "BIL-T", "BIL-D", "BIL-I", "ALP", "PROT-T"
    ]
    expected_child_ids = [tests_by_code[c].id for c in expected_child_codes]
    assert set(pack.childTestIds) == set(expected_child_ids)

    # 4. Validar existencia de cuentas comerciales para ORIGIN_BRANCH
    for code in expected_codes:
        test = tests_by_code[code]
        account = await accounts_repo.get_by_branch_and_test(ORIGIN_BRANCH_ID, test.id)
        assert account is not None, f"Debe existir LabTestAccount para {code} en ORIGIN_BRANCH."

    # 5. Probar Idempotencia: ejecutar nuevamente no debe duplicar registros
    count_before = len(await lab_tests_repo.get_all_lab_tests())
    await create_default_lab_tests()
    count_after = len(await lab_tests_repo.get_all_lab_tests())

    assert count_before == count_after, "La ejecución repetida de create_default_lab_tests no debe duplicar exámenes."
