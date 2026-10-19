import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from serum.core.default_values.create_default_branch import ORIGIN_BRANCH_ID
from serum.repos.v1._shared_models import ReferenceValue
from serum.repos.v1.branches import BranchesRepository
from serum.repos.v1.lab_test_accounts import (
    CreateLabTestAccount,
    LabTestAccountsRepository,
    LabTestCommercial,
)
from serum.repos.v1.lab_tests import (
    CreateLabTest,
    LabTestInDb,
    LabTestsRepository,
    UpdateLabTest,
)

logger = logging.getLogger("serum.default_values")


class ImportCatalogResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    message: str = "Catálogo por defecto importado exitosamente"
    atomicCreated: int = 0
    packsCreated: int = 0
    accountsCreated: int = 0
    alreadyExisting: int = 0
    totalProcessed: int = 0



def _normalize_gender(g: str) -> str:
    lower = g.strip().lower()
    if lower in ("f", "female", "femenino"):
        return "female"
    if lower in ("m", "male", "masculino"):
        return "male"
    return "both"


def _normalize_reference_values(ref_values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for rv in ref_values:
        item = dict(rv)
        if "gender" in item and isinstance(item["gender"], str):
            item["gender"] = _normalize_gender(item["gender"])
        normalized.append(item)
    return normalized


def _resolve_static_file_path() -> Path | None:
    current = Path(__file__).resolve().parent
    for _ in range(8):
        for candidate in (
            current / "app" / "static" / "lab_tests_master.json",
            current / "static" / "lab_tests_master.json",
        ):
            if candidate.exists():
                return candidate
            if current.parent == current:
                break
            current = current.parent

    for rel in (
        Path("app/static/lab_tests_master.json"),
        Path("static/lab_tests_master.json"),
    ):
        if rel.exists():
            return rel.resolve()

    return None


def _register_and_build_accounts(
    created_tests: list[LabTestInDb],
    active_branch_ids: list[str],
    existing_by_code: dict[str, LabTestInDb],
    existing_by_name: dict[str, LabTestInDb],
) -> list[CreateLabTestAccount]:
    """Registra pruebas creadas en los índices en memoria y genera cuentas comerciales por sucursal."""
    accounts: list[CreateLabTestAccount] = []
    for test in created_tests:
        if test.code:
            existing_by_code[test.code] = test
        if test.name:
            existing_by_name[test.name.strip().lower()] = test

        origin_comm = LabTestCommercial(
            salePrice=test.salePrice,
            salePrice2=test.salePrice2,
            costPrice=test.costPrice,
            currency=test.currency,
        )
        accounts.append(
            CreateLabTestAccount(
                branchId=ORIGIN_BRANCH_ID,
                labTestId=test.id,
                commercial=origin_comm,
            )
        )
        for branch_id in active_branch_ids:
            if branch_id != ORIGIN_BRANCH_ID:
                accounts.append(
                    CreateLabTestAccount(
                        branchId=branch_id,
                        labTestId=test.id,
                        commercial=LabTestCommercial(
                            salePrice=0,
                            salePrice2=0,
                            costPrice=0,
                            currency=test.currency,
                        ),
                    )
                )
    return accounts


async def create_default_lab_tests(
    json_path: Path | None = None,
) -> ImportCatalogResult:
    """Carga e inicializa el catálogo de LabTests desde el archivo estático si no existen.
    
    Procesa en 2 fases:
    1. Pruebas individuales/atómicas (isPack: False)
    2. Packs/Perfiles (isPack: True), resolviendo childTestCodes -> childTestIds
    """
    if json_path is None:
        json_path = _resolve_static_file_path()

    if json_path is None or not json_path.exists():
        msg = f"No se encontró el archivo estático lab_tests_master.json ({json_path})"
        logger.warning(msg)
        return ImportCatalogResult(success=False, message=msg)

    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            catalog_items: list[dict[str, Any]] = json.load(f)
    except Exception as e:
        msg = f"Error al leer {json_path}: {e}"
        logger.error(msg)
        return ImportCatalogResult(success=False, message=msg)


    lab_tests_repo = LabTestsRepository.get_instance()
    accounts_repo = LabTestAccountsRepository.get_instance()
    branches_repo = BranchesRepository.get_instance()

    # Obtener sucursales activas (para crear cuentas comerciales)
    branches = await branches_repo.get_all_branches()
    active_branch_ids = [b.id for b in branches] if branches else [ORIGIN_BRANCH_ID]
    if ORIGIN_BRANCH_ID not in active_branch_ids:
        active_branch_ids.append(ORIGIN_BRANCH_ID)

    # Obtener pruebas existentes para evitar duplicados
    existing_tests = await lab_tests_repo.get_all_lab_tests()
    existing_by_code: dict[str, LabTestInDb] = {
        t.code: t for t in existing_tests if t.code
    }
    existing_by_name: dict[str, LabTestInDb] = {
        t.name.strip().lower(): t for t in existing_tests if t.name
    }

    # Conjuntos para evitar duplicados dentro del mismo lote/archivo JSON
    queued_codes: set[str] = set()
    queued_names: set[str] = set()

    already_existing_count = 0
    total_accounts_created = 0
    created_atomics_count = 0
    created_packs_count = 0

    atomic_items = [item for item in catalog_items if not item.get("isPack", False)]
    pack_items = [item for item in catalog_items if item.get("isPack", False)]

    # --- FASE 1: Preparar e insertar pruebas atómicas en lote ---
    atomic_dtos: list[CreateLabTest] = []

    for item in atomic_items:
        code = item.get("code")
        name = item.get("name", "")
        normalized_name = name.strip().lower()

        already_exists = (
            (code and (code in existing_by_code or code in queued_codes))
            or (normalized_name in existing_by_name or normalized_name in queued_names)
        )
        if already_exists:
            already_existing_count += 1
            target_test = (
                existing_by_code.get(code)
                if code
                else existing_by_name.get(normalized_name)
            )
            if target_test and any(
                _normalize_gender(rv.gender) != rv.gender
                for rv in target_test.referenceValues
            ):
                updated_rvs = [
                    ReferenceValue(
                        patientType=rv.patientType,
                        gender=_normalize_gender(rv.gender),
                        minAgeDays=rv.minAgeDays,
                        maxAgeDays=rv.maxAgeDays,
                        minValue=rv.minValue,
                        maxValue=rv.maxValue,
                    )
                    for rv in target_test.referenceValues
                ]
                await lab_tests_repo.update_lab_test_by_id(
                    target_test.id,
                    UpdateLabTest(referenceValues=updated_rvs),
                )
            continue

        payload = dict(item)
        payload.pop("childTestCodes", None)
        payload["branchId"] = ORIGIN_BRANCH_ID
        if "referenceValues" in payload and isinstance(payload["referenceValues"], list):
            payload["referenceValues"] = _normalize_reference_values(
                payload["referenceValues"]
            )

        try:
            create_dto = CreateLabTest(**payload)
            atomic_dtos.append(create_dto)
            if create_dto.code:
                queued_codes.add(create_dto.code)
            if create_dto.name:
                queued_names.add(create_dto.name.strip().lower())
        except Exception as e:
            logger.error(f"Error al parsear prueba atómica '{name}': {e}")

    if atomic_dtos:
        created_atomics = await lab_tests_repo.create_lab_tests_batch(atomic_dtos)
        created_atomics_count = len(created_atomics)
        accounts_to_create = _register_and_build_accounts(
            created_atomics,
            active_branch_ids,
            existing_by_code,
            existing_by_name,
        )
        if accounts_to_create:
            await accounts_repo.create_accounts_batch(accounts_to_create)
            total_accounts_created += len(accounts_to_create)

    # --- FASE 2: Preparar e insertar Packs / Perfiles en lote ---
    pack_dtos: list[CreateLabTest] = []

    for pack in pack_items:
        code = pack.get("code")
        name = pack.get("name", "")
        normalized_name = name.strip().lower()
        child_codes: list[str] = pack.get("childTestCodes", [])

        # Resolver IDs a partir de los códigos ya disponibles en memoria
        child_ids: list[str] = list(pack.get("childTestIds", []))
        if not child_ids and child_codes:
            for c_code in child_codes:
                child_test = existing_by_code.get(c_code)
                if child_test:
                    child_ids.append(child_test.id)
                else:
                    logger.warning(
                        f"Pack '{name}' (código {code}): No se encontró la prueba hija con código '{c_code}'"
                    )

        already_exists = (
            (code and (code in existing_by_code or code in queued_codes))
            or (normalized_name in existing_by_name or normalized_name in queued_names)
        )

        existing_pack = None
        if code and code in existing_by_code:
            existing_pack = existing_by_code[code]
        elif normalized_name in existing_by_name:
            existing_pack = existing_by_name[normalized_name]

        if not already_exists:
            payload = dict(pack)
            payload.pop("childTestCodes", None)
            payload["childTestIds"] = child_ids
            payload["branchId"] = ORIGIN_BRANCH_ID

            try:
                create_dto = CreateLabTest(**payload)
                pack_dtos.append(create_dto)
                if create_dto.code:
                    queued_codes.add(create_dto.code)
                if create_dto.name:
                    queued_names.add(create_dto.name.strip().lower())
            except Exception as e:
                logger.error(f"Error al parsear pack por defecto '{name}': {e}")
        else:
            already_existing_count += 1
            if existing_pack is not None and not existing_pack.childTestIds and child_ids:
                try:
                    await lab_tests_repo.update_lab_test_by_id(
                        existing_pack.id,
                        UpdateLabTest(childTestIds=child_ids),
                    )
                except Exception as e:
                    logger.error(
                        f"Error al actualizar childTestIds de pack '{name}': {e}"
                    )

    if pack_dtos:
        created_packs = await lab_tests_repo.create_lab_tests_batch(pack_dtos)
        created_packs_count = len(created_packs)
        pack_accounts_to_create = _register_and_build_accounts(
            created_packs,
            active_branch_ids,
            existing_by_code,
            existing_by_name,
        )
        if pack_accounts_to_create:
            await accounts_repo.create_accounts_batch(pack_accounts_to_create)
            total_accounts_created += len(pack_accounts_to_create)

    return ImportCatalogResult(
        success=True,
        message="Catálogo por defecto importado exitosamente",
        atomicCreated=created_atomics_count,
        packsCreated=created_packs_count,
        accountsCreated=total_accounts_created,
        alreadyExisting=already_existing_count,
        totalProcessed=len(catalog_items),
    )

