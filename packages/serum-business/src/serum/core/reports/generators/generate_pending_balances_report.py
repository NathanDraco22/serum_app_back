from serum.core.reports.reports_schemas import (
    PendingBalanceItem,
    PendingBalancesBranchReport,
    PendingBalancesReportResponse,
    PendingBalancesSummary,
)
from serum.core.reports.generators.reports_helpers import get_branches_map
from serum.core.reports.reports_pipelines import ReportsPipelines
from serum.services.mongo_collections.v1 import OrdersCollection


async def generate_pending_balances_report(
    start_date: int,
    end_date: int,
    branch_id: str | None = None,
) -> PendingBalancesReportResponse:
    orders_col = OrdersCollection.get_instance()._collection
    branches_map = await get_branches_map()

    raw_data = await ReportsPipelines.aggregate_pending_balances(
        orders_col, start_date, end_date, branch_id
    )

    branch_orders: dict[str, list[PendingBalanceItem]] = {}
    total_pending_global = 0
    total_orders_count = 0

    for row in raw_data:
        b_id = row.get("branchId") or "unknown"
        pending_amt = row.get("pendingAmount", 0)
        order_date = row.get("orderDate", 0)
        days_pending = max(0, int((end_date - order_date) / 86400000))

        item = PendingBalanceItem(
            orderId=row.get("orderId", ""),
            patientId=row.get("patientId", ""),
            patientName=row.get("patientName", "Paciente"),
            patientPhone=row.get("patientPhone", ""),
            totalPrice=row.get("totalPrice", 0),
            paidAmount=row.get("paidAmount", 0),
            pendingAmount=pending_amt,
            orderDate=order_date,
            daysPending=days_pending,
        )

        total_pending_global += pending_amt
        total_orders_count += 1
        branch_orders.setdefault(b_id, []).append(item)

    by_branch_list: list[PendingBalancesBranchReport] = []
    if branch_id and branch_id not in branch_orders:
        by_branch_list.append(
            PendingBalancesBranchReport(
                branchId=branch_id,
                branchName=branches_map.get(branch_id, f"Sucursal {branch_id}"),
                totalPendingAmount=0,
                ordersCount=0,
                orders=[],
            )
        )

    for b_id, o_list in branch_orders.items():
        branch_total = sum(o.pendingAmount for o in o_list)
        by_branch_list.append(
            PendingBalancesBranchReport(
                branchId=b_id,
                branchName=branches_map.get(b_id, f"Sucursal {b_id}"),
                totalPendingAmount=branch_total,
                ordersCount=len(o_list),
                orders=o_list,
            )
        )

    summary = PendingBalancesSummary(
        totalPendingAmount=total_pending_global,
        ordersCount=total_orders_count,
    )

    return PendingBalancesReportResponse(
        startDate=start_date,
        endDate=end_date,
        summary=summary,
        byBranch=by_branch_list,
    )
