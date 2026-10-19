import pytest
from dotenv import load_dotenv

from serum.core.default_values.create_default_branch import ORIGIN_BRANCH_ID
from serum.core.default_values.create_default_lab_tests import create_default_lab_tests
from serum.services_initializer import init_services
from serum.repos.v1.lab_test_accounts import LabTestAccountsRepository
from serum.repos.v1.lab_tests import LabTestsRepository


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
        # Lote 1: Química clínica y Pruebas especiales
        "GLU", "CREA", "TGO", "TGP", "GGT",
        "BIL-T", "BIL-D", "BIL-I", "ALP", "PROT-T",
        "TSH", "T4L", "T3", "INS", "PERF-HEP",
        # Lote 2: Hematología
        "ERI", "HB", "HTC", "VCM", "HCM", "CHCM", "LEU", "PLAQ",
        "SEG", "LINF", "EOS", "MON", "BAN", "BAS", "LINF-ATIP", "BHC",
        # Lote 2: Uroanálisis (EGO)
        "COL-ORI", "ASP-ORI", "SED-ORI", "DEN-ORI", "PH-ORI", "LEU-ORI",
        "GLU-ORI", "PROT-ORI", "CET-ORI", "BIL-ORI", "SANG-ORI", "NIT-ORI",
        "URO-ORI", "CEL-EPI", "LEU-LIB", "LEU-AGR", "ERI-SED", "CRIS-ORI",
        "CIL-ORI", "BAC-ORI", "HIL-MUC", "EST-LEU", "LEV-ORI", "EGO",
        # Lote 3: Coprología y Serología
        "COL-HEC", "CONS-HEC", "MUC-HEC", "PH-HEC", "PROT-HEC", "HB-HEC",
        "PAR-HEC", "COG-HEC", "LEV-HEC", "FLOR-BAC", "PLA-ALIM", "EGH",
        "HP-HEC", "PMN-NEUT", "MN-EOS", "AZUC-RED", "TW-HEC"
    ]

    for code in expected_codes:
        assert code in tests_by_code, f"El test con código '{code}' debería haberse cargado desde static."

    # 3. Validar los Packs y la resolución de childTestIds
    # 3.1 Perfil Hepático
    pack_hep = tests_by_code["PERF-HEP"]
    assert pack_hep.isPack is True
    assert len(pack_hep.childTestIds) == 8
    expected_hep_codes = [
        "TGO", "TGP", "GGT", "BIL-T", "BIL-D", "BIL-I", "ALP", "PROT-T"
    ]
    assert set(pack_hep.childTestIds) == {tests_by_code[c].id for c in expected_hep_codes}

    # 3.2 Biometría Hemática Completa
    pack_bhc = tests_by_code["BHC"]
    assert pack_bhc.isPack is True
    assert len(pack_bhc.childTestIds) == 15
    expected_bhc_codes = [
        "ERI", "HB", "HTC", "VCM", "HCM", "CHCM", "LEU", "PLAQ",
        "SEG", "LINF", "EOS", "MON", "BAN", "BAS", "LINF-ATIP"
    ]
    assert set(pack_bhc.childTestIds) == {tests_by_code[c].id for c in expected_bhc_codes}

    # 3.3 Examen General de Orina
    pack_ego = tests_by_code["EGO"]
    assert pack_ego.isPack is True
    assert len(pack_ego.childTestIds) == 23
    expected_ego_codes = [
        "COL-ORI", "ASP-ORI", "SED-ORI", "DEN-ORI", "PH-ORI", "LEU-ORI",
        "GLU-ORI", "PROT-ORI", "CET-ORI", "BIL-ORI", "SANG-ORI", "NIT-ORI",
        "URO-ORI", "CEL-EPI", "LEU-LIB", "LEU-AGR", "ERI-SED", "CRIS-ORI",
        "CIL-ORI", "BAC-ORI", "HIL-MUC", "EST-LEU", "LEV-ORI"
    ]
    assert set(pack_ego.childTestIds) == {tests_by_code[c].id for c in expected_ego_codes}

    # 3.4 Examen General de Heces
    pack_egh = tests_by_code["EGH"]
    assert pack_egh.isPack is True
    assert len(pack_egh.childTestIds) == 11
    expected_egh_codes = [
        "COL-HEC", "CONS-HEC", "MUC-HEC", "PH-HEC", "PROT-HEC", "HB-HEC",
        "PAR-HEC", "COG-HEC", "LEV-HEC", "FLOR-BAC", "PLA-ALIM"
    ]
    assert set(pack_egh.childTestIds) == {tests_by_code[c].id for c in expected_egh_codes}

    # 3.5 Tinción de Wright en Heces
    pack_tw = tests_by_code["TW-HEC"]
    assert pack_tw.isPack is True
    assert len(pack_tw.childTestIds) == 6
    expected_tw_codes = [
        "COL-HEC", "CONS-HEC", "MUC-HEC", "PMN-NEUT", "MN-EOS", "AZUC-RED"
    ]
    assert set(pack_tw.childTestIds) == {tests_by_code[c].id for c in expected_tw_codes}

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
