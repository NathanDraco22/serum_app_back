from fastapi import APIRouter, Depends

from serum.core.default_values import ImportCatalogResult, UpdateImportResult

from .imports_controller import (
    ImportBranchPricesRequest,
    ImportBranchPricesResult,
    ReferenceValuesMigrationRequest,
    ReferenceValuesMigrationResult,
    UpdateImportRequest,
    imports_controller,
)
from .imports_depends import validate_admin_or_super_token

imports_router = APIRouter(
    tags=["importsV1"],
    dependencies=[Depends(validate_admin_or_super_token)],
)


@imports_router.post("/default-catalog", response_model=ImportCatalogResult)
async def import_default_catalog() -> ImportCatalogResult:
    """Activa o re-ejecuta la importación del catálogo por defecto para el tenant actual."""
    return await imports_controller.import_default_catalog()


@imports_router.post("/lab-tests", response_model=ImportCatalogResult)
async def import_lab_tests_alias() -> ImportCatalogResult:
    """Alias para importar el catálogo de pruebas por defecto."""
    return await imports_controller.import_default_catalog()


@imports_router.post("/update-catalog", response_model=UpdateImportResult)
async def update_catalog(
    request: UpdateImportRequest,
) -> UpdateImportResult:
    """Actualiza y sincroniza las pruebas y packs desde el catálogo estático maestro (preservando precios por defecto)."""
    return await imports_controller.update_catalog(request)


@imports_router.post("/sync-catalog", response_model=UpdateImportResult)
async def sync_catalog_alias(
    request: UpdateImportRequest,
) -> UpdateImportResult:
    """Alias para actualizar y sincronizar el catálogo desde el archivo estático maestro."""
    return await imports_controller.update_catalog(request)


@imports_router.post("/reference-values", response_model=ReferenceValuesMigrationResult)
async def migrate_reference_values(
    request: ReferenceValuesMigrationRequest,
) -> ReferenceValuesMigrationResult:
    """Actualiza únicamente los referenceValues de las pruebas indicadas por code."""
    return await imports_controller.migrate_reference_values(request)


@imports_router.post("/branch-prices", response_model=ImportBranchPricesResult)
async def import_branch_prices(
    request: ImportBranchPricesRequest,
) -> ImportBranchPricesResult:
    """Importa precios de exámenes clínicos desde una sucursal origen hacia una sucursal destino."""
    return await imports_controller.import_branch_prices(request)
