from pymongo import IndexModel

from serum.services.mongo_collections.v1 import (
    CashShiftsCollection,
    CashTransactionsCollection,
    OrdersCollection,
    QuotationsCollection,
)


async def ensure_reports_indexes(nickname: str | None = None) -> None:
    # 1. Colección Orders
    orders_col = OrdersCollection.get_instance(nickname)._collection
    await orders_col.create_indexes(
        [
            IndexModel(
                [("isDeleted", 1), ("createdAt", -1), ("branchId", 1)],
                name="idx_orders_reports_dates_branch",
            ),
            IndexModel(
                [
                    ("isDeleted", 1),
                    ("branchId", 1),
                    ("doctorId", 1),
                    ("createdAt", -1),
                ],
                name="idx_orders_reports_doctors",
            ),
            IndexModel(
                [
                    ("isDeleted", 1),
                    ("branchId", 1),
                    ("items.labTestId", 1),
                    ("createdAt", -1),
                ],
                name="idx_orders_reports_items",
            ),
        ]
    )

    # 2. Colección CashTransactions
    transactions_col = CashTransactionsCollection.get_instance(nickname)._collection
    await transactions_col.create_indexes(
        [
            IndexModel(
                [
                    ("isDeleted", 1),
                    ("branchId", 1),
                    ("flowType", 1),
                    ("subType", 1),
                    ("createdAt", -1),
                ],
                name="idx_cash_transactions_reports",
            ),
        ]
    )

    # 3. Colección CashShifts
    shifts_col = CashShiftsCollection.get_instance(nickname)._collection
    await shifts_col.create_indexes(
        [
            IndexModel(
                [
                    ("isDeleted", 1),
                    ("branchId", 1),
                    ("status", 1),
                    ("closedAt", -1),
                ],
                name="idx_cash_shifts_reports_closed",
            ),
        ]
    )

    # 4. Colección Quotations
    quotations_col = QuotationsCollection.get_instance(nickname)._collection
    await quotations_col.create_indexes(
        [
            IndexModel(
                [("isDeleted", 1), ("branchId", 1), ("createdAt", -1)],
                name="idx_quotations_reports_dates",
            ),
        ]
    )
