from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict

from serum.core.default_values import ImportCatalogResult, create_default_lab_tests
from serum.repos.v1.branches import BranchesRepository
from serum.repos.v1.lab_test_accounts import (
    CreateLabTestAccount,
    LabTestAccountsRepository,
    LabTestCommercial,
    UpdateLabTestAccountCommercial,
)
from serum.repos.v1.lab_tests import LabTestsRepository


class ImportBranchPricesRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sourceBranchId: str
    targetBranchId: str
    mustOverridePrice: bool = False


class ImportBranchPricesResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    message: str = "Precios importados exitosamente"
    sourceBranchId: str
    sourceBranchName: str
    targetBranchId: str
    targetBranchName: str
    mustOverridePrice: bool = False
    totalEvaluated: int = 0
    updatedCount: int = 0
    createdCount: int = 0
    skippedCount: int = 0


class ImportsController:
    async def import_default_catalog(self) -> ImportCatalogResult:
        """Activa o re-ejecuta la importación del catálogo por defecto para el tenant actual."""
        result = await create_default_lab_tests()
        return result

    async def import_branch_prices(
        self, request: ImportBranchPricesRequest
    ) -> ImportBranchPricesResult:
        """Importa precios de exámenes clínicos desde una sucursal origen hacia una sucursal destino."""
        source_id = request.sourceBranchId.strip()
        target_id = request.targetBranchId.strip()

        if not source_id or not target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se deben proporcionar las sucursales de origen y destino.",
            )

        if source_id == target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La sucursal origen y la sucursal destino no pueden ser la misma.",
            )

        branches_repo = BranchesRepository.get_instance()
        source_branch = await branches_repo.get_branch_by_id(source_id)
        target_branch = await branches_repo.get_branch_by_id(target_id)

        if source_branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La sucursal de origen '{source_id}' no existe.",
            )

        if target_branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La sucursal de destino '{target_id}' no existe.",
            )

        lab_tests_repo = LabTestsRepository.get_instance()
        accounts_repo = LabTestAccountsRepository.get_instance()

        source_tests = await lab_tests_repo.get_all_lab_tests(branchId=source_id)
        target_tests = await lab_tests_repo.get_all_lab_tests(branchId=target_id)
        target_dict = {t.id: t for t in target_tests}

        target_accounts = {
            acc.labTestId: acc
            for acc in await accounts_repo.get_by_branch(branchId=target_id)
        }

        total_evaluated = 0
        updated_count = 0
        created_count = 0
        skipped_count = 0

        for src_test in source_tests:
            total_evaluated += 1
            tgt_test = target_dict.get(src_test.id)
            if tgt_test is None:
                skipped_count += 1
                continue

            existing_account = target_accounts.get(src_test.id)

            if request.mustOverridePrice:
                new_sale = src_test.salePrice
                new_sale2 = src_test.salePrice2
                new_cost = src_test.costPrice
                new_currency = src_test.currency or "USD"

                has_changed = (
                    tgt_test.salePrice != new_sale
                    or tgt_test.salePrice2 != new_sale2
                    or tgt_test.costPrice != new_cost
                    or tgt_test.currency != new_currency
                )

                if existing_account is not None:
                    if has_changed:
                        await accounts_repo.update_commercial_by_branch_and_test(
                            branchId=target_id,
                            labTestId=src_test.id,
                            update_model=UpdateLabTestAccountCommercial(
                                salePrice=new_sale,
                                salePrice2=new_sale2,
                                costPrice=new_cost,
                                currency=new_currency,
                            ),
                        )
                        updated_count += 1
                    else:
                        skipped_count += 1
                else:
                    await accounts_repo.create_account(
                        CreateLabTestAccount(
                            branchId=target_id,
                            labTestId=src_test.id,
                            commercial=LabTestCommercial(
                                salePrice=new_sale,
                                salePrice2=new_sale2,
                                costPrice=new_cost,
                                currency=new_currency,
                            ),
                        )
                    )
                    created_count += 1
            else:
                # Solo actualizar valores en 0
                new_sale = (
                    src_test.salePrice
                    if tgt_test.salePrice == 0 and src_test.salePrice > 0
                    else tgt_test.salePrice
                )
                new_sale2 = (
                    src_test.salePrice2
                    if tgt_test.salePrice2 == 0 and src_test.salePrice2 > 0
                    else tgt_test.salePrice2
                )
                new_cost = (
                    src_test.costPrice
                    if tgt_test.costPrice == 0 and src_test.costPrice > 0
                    else tgt_test.costPrice
                )
                new_currency = (
                    src_test.currency
                    if (tgt_test.salePrice == 0 and src_test.currency)
                    else (tgt_test.currency or "USD")
                )

                has_changed = (
                    new_sale != tgt_test.salePrice
                    or new_sale2 != tgt_test.salePrice2
                    or new_cost != tgt_test.costPrice
                )

                if has_changed:
                    if existing_account is not None:
                        await accounts_repo.update_commercial_by_branch_and_test(
                            branchId=target_id,
                            labTestId=src_test.id,
                            update_model=UpdateLabTestAccountCommercial(
                                salePrice=new_sale,
                                salePrice2=new_sale2,
                                costPrice=new_cost,
                                currency=new_currency,
                            ),
                        )
                        updated_count += 1
                    else:
                        await accounts_repo.create_account(
                            CreateLabTestAccount(
                                branchId=target_id,
                                labTestId=src_test.id,
                                commercial=LabTestCommercial(
                                    salePrice=new_sale,
                                    salePrice2=new_sale2,
                                    costPrice=new_cost,
                                    currency=new_currency,
                                ),
                            )
                        )
                        created_count += 1
                else:
                    skipped_count += 1

        msg = (
            f"Se importaron exitosamente los precios desde '{source_branch.name}' "
            f"hacia '{target_branch.name}' (Modo: {'Sobrescribir' if request.mustOverridePrice else 'Actualizar valores en 0'})."
        )

        return ImportBranchPricesResult(
            success=True,
            message=msg,
            sourceBranchId=source_id,
            sourceBranchName=source_branch.name,
            targetBranchId=target_id,
            targetBranchName=target_branch.name,
            mustOverridePrice=request.mustOverridePrice,
            totalEvaluated=total_evaluated,
            updatedCount=updated_count,
            createdCount=created_count,
            skippedCount=skipped_count,
        )


imports_controller = ImportsController()
