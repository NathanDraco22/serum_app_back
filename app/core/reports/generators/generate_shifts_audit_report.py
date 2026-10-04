from typing import Any

from api.v1.reports.reports_schemas import (
    ShiftAuditItem,
    ShiftsAuditBranchReport,
    ShiftsAuditReportResponse,
    ShiftsAuditSummary,
)
from core.reports.generators.reports_helpers import (
    get_branches_map,
    get_users_map,
)
from services.mongo_collections.v1 import CashShiftsCollection


async def generate_shifts_audit_report(
    start_date: int,
    end_date: int,
    branch_id: str | None = None,
    only_discrepancies: bool = False,
) -> ShiftsAuditReportResponse:
    shifts_col = CashShiftsCollection.get_instance()._collection
    branches_map = await get_branches_map()
    users_map = await get_users_map()

    query: dict[str, Any] = {
        "isDeleted": {"$ne": True},
        "status": "CLOSED",
        "closedAt": {"$gte": start_date, "$lte": end_date},
    }
    if branch_id:
        query["branchId"] = branch_id
    if only_discrepancies:
        query["difference"] = {"$ne": 0}

    cursor = shifts_col.find(query).sort("closedAt", -1)
    shifts_data = await cursor.to_list(length=None)
    await cursor.close()

    branch_shifts: dict[str, list[ShiftAuditItem]] = {}
    total_shifts_global = 0
    total_discrepancies_global = 0
    net_diff_global = 0

    for s in shifts_data:
        b_id = s.get("branchId") or "unknown"
        diff = s.get("difference")
        has_disc = diff is not None and diff != 0

        total_shifts_global += 1
        if has_disc:
            total_discrepancies_global += 1
        if diff:
            net_diff_global += diff

        u_id = s.get("userId", "")
        item = ShiftAuditItem(
            shiftId=s.get("id", ""),
            userId=u_id,
            userName=users_map.get(u_id, u_id),
            openedAt=s.get("openedAt", 0),
            closedAt=s.get("closedAt"),
            initialBalance=s.get("initialBalance", 0),
            cashBalance=s.get("cashBalance", 0),
            cardBalance=s.get("cardBalance", 0),
            transferBalance=s.get("transferBalance", 0),
            totalBalance=s.get("totalBalance", 0),
            declaredCash=s.get("declaredCash"),
            difference=diff,
            notes=s.get("notes", ""),
        )
        branch_shifts.setdefault(b_id, []).append(item)

    by_branch_list: list[ShiftsAuditBranchReport] = []
    if branch_id and branch_id not in branch_shifts:
        by_branch_list.append(
            ShiftsAuditBranchReport(
                branchId=branch_id,
                branchName=branches_map.get(branch_id, f"Sucursal {branch_id}"),
                totalShifts=0,
                totalDiscrepancies=0,
                netDifference=0,
                shifts=[],
            )
        )

    for b_id, s_list in branch_shifts.items():
        b_disc = sum(
            1 for x in s_list if x.difference is not None and x.difference != 0
        )
        b_net = sum(x.difference or 0 for x in s_list)
        by_branch_list.append(
            ShiftsAuditBranchReport(
                branchId=b_id,
                branchName=branches_map.get(b_id, f"Sucursal {b_id}"),
                totalShifts=len(s_list),
                totalDiscrepancies=b_disc,
                netDifference=b_net,
                shifts=s_list,
            )
        )

    summary = ShiftsAuditSummary(
        totalShifts=total_shifts_global,
        totalDiscrepancies=total_discrepancies_global,
        netDifference=net_diff_global,
    )

    return ShiftsAuditReportResponse(
        startDate=start_date,
        endDate=end_date,
        summary=summary,
        byBranch=by_branch_list,
    )
