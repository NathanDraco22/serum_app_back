from fastapi import APIRouter, Depends

from serum.core.default_values import ImportCatalogResult

from .imports_controller import (
    ImportBranchPricesRequest,
    ImportBranchPricesResult,
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


@imports_router.post("/branch-prices", response_model=ImportBranchPricesResult)
async def import_branch_prices(
    request: ImportBranchPricesRequest,
) -> ImportBranchPricesResult:
    """Importa precios de exámenes clínicos desde una sucursal origen hacia una sucursal destino."""
    return await imports_controller.import_branch_prices(request)
