from api.v1.reports.reports_schemas import (
    FinancialReportResponse,
    LabTestsVolumeReportResponse,
    PendingBalancesReportResponse,
    ShiftsAuditReportResponse,
    TopDoctorsReportResponse,
)
from serum.core.reports.generators import (
    generate_financial_report,
    generate_lab_tests_volume_report,
    generate_pending_balances_report,
    generate_shifts_audit_report,
    generate_top_doctors_report,
)


class ReportsManager:
    """Orquestador fachada que centraliza y delega la ejecución de reportes

    a sus respectivos generadores en core/reports/generators/.
    """

    @staticmethod
    async def get_financial_report(
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> FinancialReportResponse:
        return await generate_financial_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
        )

    @staticmethod
    async def get_top_doctors_report(
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
        limit: int = 10,
    ) -> TopDoctorsReportResponse:
        return await generate_top_doctors_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
            limit=limit,
        )

    @staticmethod
    async def get_lab_tests_volume_report(
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
        source: str = "orders",
        limit: int = 10,
    ) -> LabTestsVolumeReportResponse:
        return await generate_lab_tests_volume_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
            source=source,
            limit=limit,
        )

    @staticmethod
    async def get_pending_balances_report(
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> PendingBalancesReportResponse:
        return await generate_pending_balances_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
        )

    @staticmethod
    async def get_shifts_audit_report(
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
        only_discrepancies: bool = False,
    ) -> ShiftsAuditReportResponse:
        return await generate_shifts_audit_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
            only_discrepancies=only_discrepancies,
        )
