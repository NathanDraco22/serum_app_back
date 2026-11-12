import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from serum.core.default_values.create_default_branch import ORIGIN_BRANCH_ID
from serum.core.default_values.create_default_lab_tests import (
    _normalize_reference_values,
    _register_and_build_accounts,
    _resolve_static_file_path,
)
from serum.repos.v1._shared_models import ReferenceValue
from serum.repos.v1.branches import BranchesRepository
from serum.repos.v1.lab_test_accounts import (
    CreateLabTestAccount,
    LabTestAccountsRepository,
    LabTestCommercial,
    UpdateLabTestAccountCommercial,
)
from serum.repos.v1.lab_tests import (
    CreateLabTest,
    LabTestInDb,
    LabTestsRepository,
    UpdateLabTest,
)

logger = logging.getLogger("serum.default_values")


class UpdateImportResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    message: str = "Catálogo actualizado exitosamente"
    totalProcessed: int = 0
    updatedTestsCount: int = 0
    createdTestsCount: int = 0
    updatedAccountsCount: int = 0
    createdAccountsCount: int = 0
    skippedPricesCount: int = 0
    preservedReferenceValuesCount: int = 0


async def update_default_lab_tests(
    override_price: bool = False,
    preserve_reference_values: bool = True,
    json_path: Path | None = None,
) -> UpdateImportResult:
    """Actualiza y sincroniza las pruebas y packs clínicos desde el archivo estático maestro.

    - Si override_price es False:
      Se actualizan nombres, subclasificaciones, categorías, tipos de datos, unidades de medida,
      opciones cualitativas y relaciones de packs (childTestIds),
      pero SE PRESERVAN INTACTOS los precios de venta y costo existentes.
    - Si override_price es True:
      Se sobreescriben también los precios en LabTest y en las cuentas comerciales (LabTestAccount).
    - Si preserve_reference_values es True (recomendado):
      NO se sobreescriben los referenceValues de las pruebas existentes. Las pruebas nuevas
      se crean con los valores del maestro.
    - Si el archivo contiene pruebas o packs nuevos que no existían previamente, se dan de alta limpiamente.
    """
    if json_path is None:
        json_path = _resolve_static_file_path()

    if json_path is None or not json_path.exists():
        msg = f"No se encontró el archivo estático lab_tests_master.json ({json_path})"
        logger.warning(msg)
        return UpdateImportResult(success=False, message=msg)

    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            catalog_items: list[dict[str, Any]] = json.load(f)
    except Exception as e:
        msg = f"Error al leer {json_path}: {e}"
        logger.error(msg)
        return UpdateImportResult(success=False, message=msg)

    lab_tests_repo = LabTestsRepository.get_instance()
    accounts_repo = LabTestAccountsRepository.get_instance()
    branches_repo = BranchesRepository.get_instance()

    # Obtener sucursales activas
    branches = await branches_repo.get_all_branches()
    active_branch_ids = [b.id for b in branches] if branches else [ORIGIN_BRANCH_ID]
    if ORIGIN_BRANCH_ID not in active_branch_ids:
        active_branch_ids.append(ORIGIN_BRANCH_ID)

    # Obtener pruebas existentes
    existing_tests = await lab_tests_repo.get_all_lab_tests()
    existing_by_code: dict[str, LabTestInDb] = {
        t.code: t for t in existing_tests if t.code
    }
    existing_by_name: dict[str, LabTestInDb] = {
        t.name.strip().lower(): t for t in existing_tests if t.name
    }

    # Registro en memoria de cuentas existentes (branchId, labTestId)
    all_accounts = await accounts_repo.get_all()
    existing_account_pairs: set[tuple[str, str]] = {
        (acc.branchId, acc.labTestId) for acc in all_accounts
    }

    updated_tests_count = 0
    created_tests_count = 0
    updated_accounts_count = 0
    created_accounts_count = 0
    skipped_prices_count = 0
    preserved_reference_values_count = 0

    atomic_items = [item for item in catalog_items if not item.get("isPack", False)]
    pack_items = [item for item in catalog_items if item.get("isPack", False)]

    # --- FASE 1: Procesar Pruebas Atómicas ---
    new_atomic_dtos: list[CreateLabTest] = []
    atomic_update_tasks = []
    account_update_tasks = []
    missing_accounts_to_create: list[CreateLabTestAccount] = []

    for item in atomic_items:
        code = item.get("code")
        name = item.get("name", "")
        norm_name = name.strip().lower()

        existing_test = (
            existing_by_code.get(code)
            if code
            else existing_by_name.get(norm_name)
        )

        if existing_test is not None:
            update_data: dict[str, Any] = {
                "name": name or existing_test.name,
                "code": code or existing_test.code,
                "commercialCategory": item.get(
                    "commercialCategory", existing_test.commercialCategory
                ),
                "subclassification": item.get(
                    "subclassification", existing_test.subclassification
                ),
                "dataType": item.get("dataType", existing_test.dataType),
                "unitOfMeasure": item.get(
                    "unitOfMeasure", existing_test.unitOfMeasure
                ),
                "qualitativeOptions": item.get(
                    "qualitativeOptions", existing_test.qualitativeOptions
                ),
                "expectedQualitativeValue": item.get(
                    "expectedQualitativeValue", existing_test.expectedQualitativeValue
                ),
                "referenceText": item.get(
                    "referenceText", existing_test.referenceText
                ),
                "isProfileParameter": item.get(
                    "isProfileParameter", existing_test.isProfileParameter
                ),
                "isPack": False,
            }

            if "referenceValues" in item and isinstance(item["referenceValues"], list):
                if preserve_reference_values:
                    preserved_reference_values_count += 1
                else:
                    norm_refs = _normalize_reference_values(item["referenceValues"])
                    update_data["referenceValues"] = [
                        ReferenceValue(**rv) for rv in norm_refs
                    ]

            if override_price:
                new_sale = item.get("salePrice", 0)
                new_sale2 = item.get("salePrice2", 0)
                new_cost = item.get("costPrice", 0)
                new_currency = item.get("currency", "USD")

                update_data["salePrice"] = new_sale
                update_data["salePrice2"] = new_sale2
                update_data["costPrice"] = new_cost
                update_data["currency"] = new_currency

                account_update_tasks.append(
                    accounts_repo.update_commercial_by_branch_and_test(
                        branchId=ORIGIN_BRANCH_ID,
                        labTestId=existing_test.id,
                        update_model=UpdateLabTestAccountCommercial(
                            salePrice=new_sale,
                            salePrice2=new_sale2,
                            costPrice=new_cost,
                            currency=new_currency,
                        ),
                    )
                )
            else:
                skipped_prices_count += 1

            update_dto = UpdateLabTest(**update_data)
            atomic_update_tasks.append(
                lab_tests_repo.update_lab_test_by_id(existing_test.id, update_dto)
            )

            # Asegurar cuentas comerciales en todas las sedes activas si faltaban
            for b_id in active_branch_ids:
                if (b_id, existing_test.id) not in existing_account_pairs:
                    sale_val = (
                        existing_test.salePrice if b_id == ORIGIN_BRANCH_ID else 0
                    )
                    sale2_val = (
                        existing_test.salePrice2 if b_id == ORIGIN_BRANCH_ID else 0
                    )
                    cost_val = (
                        existing_test.costPrice if b_id == ORIGIN_BRANCH_ID else 0
                    )
                    missing_accounts_to_create.append(
                        CreateLabTestAccount(
                            branchId=b_id,
                            labTestId=existing_test.id,
                            commercial=LabTestCommercial(
                                salePrice=sale_val,
                                salePrice2=sale2_val,
                                costPrice=cost_val,
                                currency=existing_test.currency,
                            ),
                        )
                    )
                    existing_account_pairs.add((b_id, existing_test.id))
        else:
            payload = dict(item)
            payload.pop("childTestCodes", None)
            payload["branchId"] = ORIGIN_BRANCH_ID
            if "referenceValues" in payload and isinstance(payload["referenceValues"], list):
                payload["referenceValues"] = _normalize_reference_values(
                    payload["referenceValues"]
                )
            try:
                create_dto = CreateLabTest(**payload)
                new_atomic_dtos.append(create_dto)
            except Exception as e:
                logger.error(f"Error al parsear nueva prueba atómica '{name}': {e}")

    # Ejecutar actualizaciones atómicas en paralelo
    if atomic_update_tasks:
        updated_results = await asyncio.gather(*atomic_update_tasks)
        for ut in updated_results:
            if ut:
                updated_tests_count += 1
                if ut.code:
                    existing_by_code[ut.code] = ut
                if ut.name:
                    existing_by_name[ut.name.strip().lower()] = ut

    if account_update_tasks:
        await asyncio.gather(*account_update_tasks)
        updated_accounts_count += len(account_update_tasks)

    if missing_accounts_to_create:
        await accounts_repo.create_accounts_batch(missing_accounts_to_create)
        created_accounts_count += len(missing_accounts_to_create)

    if new_atomic_dtos:
        created_atomics = await lab_tests_repo.create_lab_tests_batch(new_atomic_dtos)
        created_tests_count += len(created_atomics)
        accounts_to_create = _register_and_build_accounts(
            created_atomics,
            active_branch_ids,
            existing_by_code,
            existing_by_name,
        )
        if accounts_to_create:
            await accounts_repo.create_accounts_batch(accounts_to_create)
            created_accounts_count += len(accounts_to_create)
            for acc in accounts_to_create:
                existing_account_pairs.add((acc.branchId, acc.labTestId))

    # --- FASE 2: Procesar Packs / Perfiles ---
    new_pack_dtos: list[CreateLabTest] = []
    pack_update_tasks = []
    pack_account_update_tasks = []
    missing_pack_accounts: list[CreateLabTestAccount] = []

    for pack in pack_items:
        code = pack.get("code")
        name = pack.get("name", "")
        norm_name = name.strip().lower()
        child_codes: list[str] = pack.get("childTestCodes", [])

        # Sincronizar childTestIds resolviendo childTestCodes desde el índice actualizado en memoria
        child_ids: list[str] = []
        if child_codes:
            for c_code in child_codes:
                child_test = existing_by_code.get(c_code)
                if child_test:
                    child_ids.append(child_test.id)
                else:
                    logger.warning(
                        f"Pack '{name}' (código {code}): No se encontró la prueba hija con código '{c_code}'"
                    )
        else:
            child_ids = list(pack.get("childTestIds", []))

        existing_pack = (
            existing_by_code.get(code)
            if code
            else existing_by_name.get(norm_name)
        )

        if existing_pack is not None:
            pack_update_data: dict[str, Any] = {
                "name": name or existing_pack.name,
                "code": code or existing_pack.code,
                "commercialCategory": pack.get(
                    "commercialCategory", existing_pack.commercialCategory
                ),
                "subclassification": pack.get(
                    "subclassification", existing_pack.subclassification
                ),
                "isPack": True,
                "useChildTestsPriceSum": pack.get(
                    "useChildTestsPriceSum", existing_pack.useChildTestsPriceSum
                ),
                "childTestIds": child_ids,
                "dataType": pack.get("dataType", existing_pack.dataType),
                "isProfileParameter": pack.get(
                    "isProfileParameter", existing_pack.isProfileParameter
                ),
            }

            if override_price:
                new_sale = pack.get("salePrice", 0)
                new_sale2 = pack.get("salePrice2", 0)
                new_cost = pack.get("costPrice", 0)
                new_currency = pack.get("currency", "USD")

                pack_update_data["salePrice"] = new_sale
                pack_update_data["salePrice2"] = new_sale2
                pack_update_data["costPrice"] = new_cost
                pack_update_data["currency"] = new_currency

                pack_account_update_tasks.append(
                    accounts_repo.update_commercial_by_branch_and_test(
                        branchId=ORIGIN_BRANCH_ID,
                        labTestId=existing_pack.id,
                        update_model=UpdateLabTestAccountCommercial(
                            salePrice=new_sale,
                            salePrice2=new_sale2,
                            costPrice=new_cost,
                            currency=new_currency,
                        ),
                    )
                )
            else:
                skipped_prices_count += 1

            update_pack_dto = UpdateLabTest(**pack_update_data)
            pack_update_tasks.append(
                lab_tests_repo.update_lab_test_by_id(existing_pack.id, update_pack_dto)
            )

            # Asegurar cuentas comerciales del pack
            for b_id in active_branch_ids:
                if (b_id, existing_pack.id) not in existing_account_pairs:
                    sale_val = (
                        existing_pack.salePrice if b_id == ORIGIN_BRANCH_ID else 0
                    )
                    sale2_val = (
                        existing_pack.salePrice2 if b_id == ORIGIN_BRANCH_ID else 0
                    )
                    cost_val = (
                        existing_pack.costPrice if b_id == ORIGIN_BRANCH_ID else 0
                    )
                    missing_pack_accounts.append(
                        CreateLabTestAccount(
                            branchId=b_id,
                            labTestId=existing_pack.id,
                            commercial=LabTestCommercial(
                                salePrice=sale_val,
                                salePrice2=sale2_val,
                                costPrice=cost_val,
                                currency=existing_pack.currency,
                            ),
                        )
                    )
                    existing_account_pairs.add((b_id, existing_pack.id))
        else:
            payload = dict(pack)
            payload.pop("childTestCodes", None)
            payload["childTestIds"] = child_ids
            payload["branchId"] = ORIGIN_BRANCH_ID

            try:
                create_dto = CreateLabTest(**payload)
                new_pack_dtos.append(create_dto)
            except Exception as e:
                logger.error(f"Error al parsear nuevo pack '{name}': {e}")

    # Ejecutar actualizaciones de packs en paralelo
    if pack_update_tasks:
        updated_pack_results = await asyncio.gather(*pack_update_tasks)
        for up in updated_pack_results:
            if up:
                updated_tests_count += 1
                if up.code:
                    existing_by_code[up.code] = up
                if up.name:
                    existing_by_name[up.name.strip().lower()] = up

    if pack_account_update_tasks:
        await asyncio.gather(*pack_account_update_tasks)
        updated_accounts_count += len(pack_account_update_tasks)

    if missing_pack_accounts:
        await accounts_repo.create_accounts_batch(missing_pack_accounts)
        created_accounts_count += len(missing_pack_accounts)

    if new_pack_dtos:
        created_packs = await lab_tests_repo.create_lab_tests_batch(new_pack_dtos)
        created_tests_count += len(created_packs)
        pack_accounts = _register_and_build_accounts(
            created_packs,
            active_branch_ids,
            existing_by_code,
            existing_by_name,
        )
        if pack_accounts:
            await accounts_repo.create_accounts_batch(pack_accounts)
            created_accounts_count += len(pack_accounts)

    return UpdateImportResult(
        success=True,
        message="Catálogo actualizado exitosamente",
        totalProcessed=len(catalog_items),
        updatedTestsCount=updated_tests_count,
        createdTestsCount=created_tests_count,
        updatedAccountsCount=updated_accounts_count,
        createdAccountsCount=created_accounts_count,
        skippedPricesCount=skipped_prices_count,
        preservedReferenceValuesCount=preserved_reference_values_count,
    )
