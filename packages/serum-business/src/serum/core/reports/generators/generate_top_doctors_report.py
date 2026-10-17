from api.v1.reports.reports_schemas import (
    DoctorOrderItem,
    TopDoctorsBranchReport,
    TopDoctorsReportResponse,
    TopDoctorsSummary,
)
from serum.core.reports.generators.reports_helpers import get_branches_map
from serum.core.reports.reports_pipelines import ReportsPipelines
from serum.services.mongo_collections.v1 import OrdersCollection


async def generate_top_doctors_report(
    start_date: int,
    end_date: int,
    branch_id: str | None = None,
    limit: int = 10,
) -> TopDoctorsReportResponse:
    orders_col = OrdersCollection.get_instance()._collection
    branches_map = await get_branches_map()

    raw_data = await ReportsPipelines.aggregate_top_doctors(
        orders_col, start_date, end_date, branch_id
    )

    branch_doctors: dict[str, list[DoctorOrderItem]] = {}
    global_doctors: dict[str, DoctorOrderItem] = {}
    total_orders_global = 0
    total_revenue_global = 0

    for row in raw_data:
        id_info = row["_id"]
        b_id = id_info.get("branchId") or "unknown"
        doc_id = id_info.get("doctorId")
        doc_name = id_info.get("doctorName") or "Sin Médico"
        specialty = id_info.get("specialty") or ""
        orders_count = row.get("totalOrders", 0)
        revenue = row.get("totalRevenue", 0)

        total_orders_global += orders_count
        total_revenue_global += revenue

        item = DoctorOrderItem(
            doctorId=doc_id,
            doctorName=doc_name,
            specialty=specialty,
            totalOrders=orders_count,
            totalRevenue=revenue,
        )

        branch_doctors.setdefault(b_id, []).append(item)

        key = f"{doc_id}_{doc_name}"
        if key not in global_doctors:
            global_doctors[key] = DoctorOrderItem(
                doctorId=doc_id,
                doctorName=doc_name,
                specialty=specialty,
                totalOrders=0,
                totalRevenue=0,
            )
        global_doctors[key].totalOrders += orders_count
        global_doctors[key].totalRevenue += revenue

    by_branch_list: list[TopDoctorsBranchReport] = []
    if branch_id and branch_id not in branch_doctors:
        by_branch_list.append(
            TopDoctorsBranchReport(
                branchId=branch_id,
                branchName=branches_map.get(branch_id, f"Sucursal {branch_id}"),
                doctors=[],
            )
        )

    for b_id, d_list in branch_doctors.items():
        sorted_docs = sorted(
            d_list, key=lambda x: (x.totalOrders, x.totalRevenue), reverse=True
        )
        by_branch_list.append(
            TopDoctorsBranchReport(
                branchId=b_id,
                branchName=branches_map.get(b_id, f"Sucursal {b_id}"),
                doctors=sorted_docs[:limit],
            )
        )

    sorted_global = sorted(
        global_doctors.values(),
        key=lambda x: (x.totalOrders, x.totalRevenue),
        reverse=True,
    )

    summary = TopDoctorsSummary(
        totalOrders=total_orders_global,
        totalRevenue=total_revenue_global,
        topDoctors=sorted_global[:limit],
    )

    return TopDoctorsReportResponse(
        startDate=start_date,
        endDate=end_date,
        summary=summary,
        byBranch=by_branch_list,
    )
