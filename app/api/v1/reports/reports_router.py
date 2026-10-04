from fastapi import APIRouter, Query

from api.v1.reports.reports_controller import reports_controller
from api.v1.reports.reports_schemas import (
    FinancialReportResponse,
    LabTestsVolumeReportResponse,
    PendingBalancesReportResponse,
    ShiftsAuditReportResponse,
    TopDoctorsReportResponse,
)

reports_router = APIRouter(tags=["reportsV1"])


@reports_router.get("/financial")
async def get_financial_report(
    start_date: int = Query(..., description="Timestamp de inicio en milisegundos"),
    end_date: int = Query(..., description="Timestamp de fin en milisegundos"),
    branch_id: str | None = Query(
        None, description="ID opcional de sucursal. Si se omite, desglosa por todas."
    ),
) -> FinancialReportResponse:
    """Reporte financiero: Total facturado vs.

    total cobrado (Kardex), métodos de pago y cuentas por cobrar.
    """
    return await reports_controller.get_financial_report(
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )


@reports_router.get("/top-doctors")
async def get_top_doctors_report(
    start_date: int = Query(..., description="Timestamp de inicio en milisegundos"),
    end_date: int = Query(..., description="Timestamp de fin en milisegundos"),
    branch_id: str | None = Query(None, description="ID opcional de sucursal"),
    limit: int = Query(
        10, ge=1, le=100, description="Cantidad máxima de médicos a listar"
    ),
) -> TopDoctorsReportResponse:
    """Reporte de médicos referentes: Cantidad de órdenes y facturación generada.

    Órdenes sin médico se catalogan como 'Sin Médico'.
    """
    return await reports_controller.get_top_doctors_report(
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
        limit=limit,
    )


@reports_router.get("/lab-tests-volume")
async def get_lab_tests_volume_report(
    start_date: int = Query(..., description="Timestamp de inicio en milisegundos"),
    end_date: int = Query(..., description="Timestamp de fin en milisegundos"),
    branch_id: str | None = Query(None, description="ID opcional de sucursal"),
    source: str = Query(
        "orders",
        description="Origen de datos: 'orders' para exámenes realizados o 'quotations' para cotizaciones",
    ),
    limit: int = Query(
        10, ge=1, le=100, description="Cantidad máxima de pruebas a listar"
    ),
) -> LabTestsVolumeReportResponse:
    """Reporte de demanda de exámenes: Pruebas y paquetes más solicitados o cotizados."""
    return await reports_controller.get_lab_tests_volume_report(
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
        source=source,
        limit=limit,
    )


@reports_router.get("/pending-balances")
async def get_pending_balances_report(
    start_date: int = Query(..., description="Timestamp de inicio en milisegundos"),
    end_date: int = Query(..., description="Timestamp de fin en milisegundos"),
    branch_id: str | None = Query(None, description="ID opcional de sucursal"),
) -> PendingBalancesReportResponse:
    """Reporte de cuentas por cobrar: Órdenes con saldo pendiente de pago."""
    return await reports_controller.get_pending_balances_report(
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )


@reports_router.get("/shifts-audit")
async def get_shifts_audit_report(
    start_date: int = Query(..., description="Timestamp de inicio en milisegundos"),
    end_date: int = Query(..., description="Timestamp de fin en milisegundos"),
    branch_id: str | None = Query(None, description="ID opcional de sucursal"),
    only_discrepancies: bool = Query(
        False,
        description="Filtrar únicamente turnos que tuvieron sobrante o faltante",
    ),
) -> ShiftsAuditReportResponse:
    """Reporte de auditoría de turnos de caja (CashShift): Control de arqueos y diferencias."""
    return await reports_controller.get_shifts_audit_report(
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
        only_discrepancies=only_discrepancies,
    )
