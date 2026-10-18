from typing import Any

from serum.core.reports.reports_schemas import (
    FinancialBranchReport,
    FinancialReportResponse,
    FinancialSummaryReport,
    PaymentMethodsBreakdown,
)
from serum.core.reports.generators.reports_helpers import get_branches_map
from serum.core.reports.reports_pipelines import ReportsPipelines
from serum.services.mongo_collections.v1 import (
    CashTransactionsCollection,
    OrdersCollection,
)


async def generate_financial_report(
    start_date: int,
    end_date: int,
    branch_id: str | None = None,
) -> FinancialReportResponse:
    orders_col = OrdersCollection.get_instance()._collection
    tx_col = CashTransactionsCollection.get_instance()._collection
    branches_map = await get_branches_map()

    orders_data = await ReportsPipelines.aggregate_orders_financial(
        orders_col, start_date, end_date, branch_id
    )
    tx_data = await ReportsPipelines.aggregate_cash_transactions(
        tx_col, start_date, end_date, branch_id
    )

    branch_reports: dict[str, dict[str, Any]] = {}

    for ord_item in orders_data:
        b_id = ord_item["_id"] or "unknown"
        branch_reports[b_id] = {
            "branchId": b_id,
            "branchName": branches_map.get(b_id, f"Sucursal {b_id}"),
            "totalBilled": ord_item.get("totalBilled", 0),
            "totalCollected": 0,
            "pendingReceivables": ord_item.get("pendingReceivables", 0),
            "ordersCount": ord_item.get("ordersCount", 0),
            "transactionsCount": 0,
            "cash": 0,
            "card": 0,
            "transfer": 0,
        }

    for tx_item in tx_data:
        b_id = tx_item["_id"].get("branchId") or "unknown"
        p_method = (tx_item["_id"].get("paymentMethod") or "cash").lower()
        amount = tx_item.get("totalAmount", 0)
        count = tx_item.get("transactionsCount", 0)

        if b_id not in branch_reports:
            branch_reports[b_id] = {
                "branchId": b_id,
                "branchName": branches_map.get(b_id, f"Sucursal {b_id}"),
                "totalBilled": 0,
                "totalCollected": 0,
                "pendingReceivables": 0,
                "ordersCount": 0,
                "transactionsCount": 0,
                "cash": 0,
                "card": 0,
                "transfer": 0,
            }

        branch_reports[b_id]["transactionsCount"] += count
        branch_reports[b_id]["totalCollected"] += amount
        if p_method == "card":
            branch_reports[b_id]["card"] += amount
        elif p_method == "transfer":
            branch_reports[b_id]["transfer"] += amount
        else:
            branch_reports[b_id]["cash"] += amount

    if branch_id and branch_id not in branch_reports:
        branch_reports[branch_id] = {
            "branchId": branch_id,
            "branchName": branches_map.get(branch_id, f"Sucursal {branch_id}"),
            "totalBilled": 0,
            "totalCollected": 0,
            "pendingReceivables": 0,
            "ordersCount": 0,
            "transactionsCount": 0,
            "cash": 0,
            "card": 0,
            "transfer": 0,
        }

    by_branch_list: list[FinancialBranchReport] = []
    global_summary = FinancialSummaryReport()

    for b_dict in branch_reports.values():
        methods = PaymentMethodsBreakdown(
            cash=b_dict["cash"],
            card=b_dict["card"],
            transfer=b_dict["transfer"],
        )
        branch_report = FinancialBranchReport(
            branchId=b_dict["branchId"],
            branchName=b_dict["branchName"],
            totalBilled=b_dict["totalBilled"],
            totalCollected=b_dict["totalCollected"],
            pendingReceivables=b_dict["pendingReceivables"],
            ordersCount=b_dict["ordersCount"],
            transactionsCount=b_dict["transactionsCount"],
            paymentMethods=methods,
        )
        by_branch_list.append(branch_report)

        global_summary.totalBilled += branch_report.totalBilled
        global_summary.totalCollected += branch_report.totalCollected
        global_summary.pendingReceivables += branch_report.pendingReceivables
        global_summary.ordersCount += branch_report.ordersCount
        global_summary.transactionsCount += branch_report.transactionsCount
        global_summary.paymentMethods.cash += methods.cash
        global_summary.paymentMethods.card += methods.card
        global_summary.paymentMethods.transfer += methods.transfer

    return FinancialReportResponse(
        startDate=start_date,
        endDate=end_date,
        summary=global_summary,
        byBranch=by_branch_list,
    )
