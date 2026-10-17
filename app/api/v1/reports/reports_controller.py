from api.v1.reports.reports_schemas import (
    FinancialReportResponse,
    LabTestsVolumeReportResponse,
    PendingBalancesReportResponse,
    ShiftsAuditReportResponse,
    TopDoctorsReportResponse,
)
from serum.core.reports.reports_manager import ReportsManager


class ReportsController:
    async def get_financial_report(
        self,
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> FinancialReportResponse:
        return await ReportsManager.get_financial_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
        )

    async def get_top_doctors_report(
        self,
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
        limit: int = 10,
    ) -> TopDoctorsReportResponse:
        return await ReportsManager.get_top_doctors_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
            limit=limit,
        )

    async def get_lab_tests_volume_report(
        self,
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
        source: str = "orders",
        limit: int = 10,
    ) -> LabTestsVolumeReportResponse:
        return await ReportsManager.get_lab_tests_volume_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
            source=source,
            limit=limit,
        )

    async def get_pending_balances_report(
        self,
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> PendingBalancesReportResponse:
        return await ReportsManager.get_pending_balances_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
        )

    async def get_shifts_audit_report(
        self,
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
        only_discrepancies: bool = False,
    ) -> ShiftsAuditReportResponse:
        return await ReportsManager.get_shifts_audit_report(
            start_date=start_date,
            end_date=end_date,
            branch_id=branch_id,
            only_discrepancies=only_discrepancies,
        )


reports_controller = ReportsController()
