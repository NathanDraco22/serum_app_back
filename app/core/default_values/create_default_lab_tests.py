import json
import logging
from pathlib import Path

from core.default_values.create_default_branch import ORIGIN_BRANCH_ID
from core.lab_tests import LabTestsManager
from repos.v1.lab_tests import (
    CreateLabTest,
    LabTestInDb,
    LabTestsRepository,
    UpdateLabTest,
)

logger = logging.getLogger("serum.default_values")


def _resolve_static_file_path() -> Path | None:
    # 1. Relative to this file: app/core/default_values -> app/static/lab_tests_master.json
    base_dir = Path(__file__).resolve().parent.parent.parent
    candidate_1 = base_dir / "static" / "lab_tests_master.json"
    if candidate_1.exists():
        return candidate_1

    # 2. Fallbacks based on CWD
    candidate_2 = Path("app/static/lab_tests_master.json").resolve()
    if candidate_2.exists():
        return candidate_2

    candidate_3 = Path("static/lab_tests_master.json").resolve()
    if candidate_3.exists():
        return candidate_3

    return None


async def create_default_lab_tests() -> None:
    """Carga e inicializa el catálogo de LabTests desde el archivo estático si no existen.
    
    Procesa en 2 fases:
    1. Pruebas individuales/atómicas (isPack: False)
    2. Packs/Perfiles (isPack: True), resolviendo childTestCodes -> childTestIds
    """
    json_path = _resolve_static_file_path()
    if json_path is None:
        logger.warning("No se encontró el archivo estático lab_tests_master.json")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            catalog_items: list[dict] = json.load(f)
    except Exception as e:
        logger.error(f"Error al leer {json_path}: {e}")
        return

    lab_tests_repo = LabTestsRepository.get_instance()
    lab_tests_manager = LabTestsManager.get_instance()

    # Obtener pruebas existentes para evitar duplicados
    existing_tests = await lab_tests_repo.get_all_lab_tests()
    existing_by_code: dict[str, LabTestInDb] = {
        t.code: t for t in existing_tests if t.code
    }
    existing_by_name: dict[str, LabTestInDb] = {
        t.name.strip().lower(): t for t in existing_tests if t.name
    }

    atomic_items = [item for item in catalog_items if not item.get("isPack", False)]
    pack_items = [item for item in catalog_items if item.get("isPack", False)]

    # Fase 1: Insertar pruebas atómicas
    for item in atomic_items:
        code = item.get("code")
        name = item.get("name", "")
        normalized_name = name.strip().lower()

        already_exists = (code and code in existing_by_code) or (
            normalized_name in existing_by_name
        )
        if already_exists:
            continue

        payload = dict(item)
        payload.pop("childTestCodes", None)
        payload["branchId"] = ORIGIN_BRANCH_ID

        try:
            create_dto = CreateLabTest(**payload)
            created_test = await lab_tests_manager.create_lab_test(create_dto)
            if created_test.code:
                existing_by_code[created_test.code] = created_test
            if created_test.name:
                existing_by_name[created_test.name.strip().lower()] = created_test
        except Exception as e:
            logger.error(f"Error al crear prueba por defecto '{name}': {e}")

    # Fase 2: Insertar o actualizar Packs y vincular childTestIds
    for pack in pack_items:
        code = pack.get("code")
        name = pack.get("name", "")
        normalized_name = name.strip().lower()
        child_codes: list[str] = pack.get("childTestCodes", [])

        # Resolver IDs a partir de los códigos
        child_ids: list[str] = list(pack.get("childTestIds", []))
        if not child_ids and child_codes:
            for c_code in child_codes:
                child_test = existing_by_code.get(c_code)
                if child_test:
                    child_ids.append(child_test.id)

        existing_pack = None
        if code and code in existing_by_code:
            existing_pack = existing_by_code[code]
        elif normalized_name in existing_by_name:
            existing_pack = existing_by_name[normalized_name]

        if existing_pack is None:
            payload = dict(pack)
            payload.pop("childTestCodes", None)
            payload["childTestIds"] = child_ids
            payload["branchId"] = ORIGIN_BRANCH_ID

            try:
                create_dto = CreateLabTest(**payload)
                created_pack = await lab_tests_manager.create_lab_test(create_dto)
                if created_pack.code:
                    existing_by_code[created_pack.code] = created_pack
                if created_pack.name:
                    existing_by_name[created_pack.name.strip().lower()] = created_pack
            except Exception as e:
                logger.error(f"Error al crear pack por defecto '{name}': {e}")
        else:
            # Si el pack ya existe pero le faltaban childTestIds, vincularlos
            if not existing_pack.childTestIds and child_ids:
                try:
                    await lab_tests_repo.update_lab_test_by_id(
                        existing_pack.id,
                        UpdateLabTest(childTestIds=child_ids),
                    )
                except Exception as e:
                    logger.error(
                        f"Error al actualizar childTestIds de pack '{name}': {e}"
                    )
