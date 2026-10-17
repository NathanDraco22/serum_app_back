from api.v1.reports.reports_schemas import (
    LabTestVolumeItem,
    LabTestsVolumeBranchReport,
    LabTestsVolumeReportResponse,
    LabTestsVolumeSummary,
)
from serum.core.reports.generators.reports_helpers import get_branches_map
from serum.core.reports.reports_pipelines import ReportsPipelines
from serum.services.mongo_collections.v1 import (
    OrdersCollection,
    QuotationsCollection,
)


async def generate_lab_tests_volume_report(
    start_date: int,
    end_date: int,
    branch_id: str | None = None,
    source: str = "orders",
    limit: int = 10,
) -> LabTestsVolumeReportResponse:
    branches_map = await get_branches_map()

    if source.lower() == "quotations":
        col = QuotationsCollection.get_instance()._collection
        raw_data = await ReportsPipelines.aggregate_quotations_lab_tests(
            col, start_date, end_date, branch_id
        )
        effective_source = "quotations"
    else:
        col = OrdersCollection.get_instance()._collection
        raw_data = await ReportsPipelines.aggregate_orders_lab_tests(
            col, start_date, end_date, branch_id
        )
        effective_source = "orders"

    branch_tests: dict[str, list[LabTestVolumeItem]] = {}
    global_tests: dict[str, LabTestVolumeItem] = {}
    total_tests_global = 0
    total_revenue_global = 0

    for row in raw_data:
        id_info = row["_id"]
        b_id = id_info.get("branchId") or "unknown"
        test_id = id_info.get("labTestId") or "unknown"
        name = id_info.get("name") or "Prueba"
        is_pack = id_info.get("isPack", False)
        times = row.get("timesOrdered", 0)
        revenue = row.get("totalRevenue", 0)

        total_tests_global += times
        total_revenue_global += revenue

        item = LabTestVolumeItem(
            labTestId=test_id,
            name=name,
            isPack=is_pack,
            timesOrdered=times,
            totalRevenue=revenue,
        )

        branch_tests.setdefault(b_id, []).append(item)

        if test_id not in global_tests:
            global_tests[test_id] = LabTestVolumeItem(
                labTestId=test_id,
                name=name,
                isPack=is_pack,
                timesOrdered=0,
                totalRevenue=0,
            )
        global_tests[test_id].timesOrdered += times
        global_tests[test_id].totalRevenue += revenue

    by_branch_list: list[LabTestsVolumeBranchReport] = []
    if branch_id and branch_id not in branch_tests:
        by_branch_list.append(
            LabTestsVolumeBranchReport(
                branchId=branch_id,
                branchName=branches_map.get(branch_id, f"Sucursal {branch_id}"),
                tests=[],
            )
        )

    for b_id, t_list in branch_tests.items():
        sorted_tests = sorted(
            t_list,
            key=lambda x: (x.timesOrdered, x.totalRevenue),
            reverse=True,
        )
        by_branch_list.append(
            LabTestsVolumeBranchReport(
                branchId=b_id,
                branchName=branches_map.get(b_id, f"Sucursal {b_id}"),
                tests=sorted_tests[:limit],
            )
        )

    sorted_global = sorted(
        global_tests.values(),
        key=lambda x: (x.timesOrdered, x.totalRevenue),
        reverse=True,
    )

    summary = LabTestsVolumeSummary(
        totalTestsCount=total_tests_global,
        totalRevenue=total_revenue_global,
        topTests=sorted_global[:limit],
    )

    return LabTestsVolumeReportResponse(
        startDate=start_date,
        endDate=end_date,
        source=effective_source,
        summary=summary,
        byBranch=by_branch_list,
    )
