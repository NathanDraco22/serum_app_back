from typing import Any
from pymongo.asynchronous.collection import AsyncCollection


class ReportsPipelines:
    @staticmethod
    async def aggregate_orders_financial(
        collection: AsyncCollection[dict[str, Any]],
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> list[dict[str, Any]]:
        match_stage: dict[str, Any] = {
            "isDeleted": {"$ne": True},
            "createdAt": {"$gte": start_date, "$lte": end_date},
        }
        if branch_id:
            match_stage["branchId"] = branch_id

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$branchId",
                    "totalBilled": {"$sum": "$totalPrice"},
                    "paidInOrders": {"$sum": "$paidAmount"},
                    "ordersCount": {"$sum": 1},
                    "pendingReceivables": {
                        "$sum": {
                            "$max": [
                                0,
                                {"$subtract": ["$totalPrice", "$paidAmount"]},
                            ]
                        }
                    },
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    @staticmethod
    async def aggregate_cash_transactions(
        collection: AsyncCollection[dict[str, Any]],
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> list[dict[str, Any]]:
        match_stage: dict[str, Any] = {
            "isDeleted": {"$ne": True},
            "createdAt": {"$gte": start_date, "$lte": end_date},
            "flowType": "in",
            "subType": "payment",
        }
        if branch_id:
            match_stage["branchId"] = branch_id

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": {
                        "branchId": "$branchId",
                        "paymentMethod": "$paymentMethod",
                    },
                    "totalAmount": {"$sum": "$amount"},
                    "transactionsCount": {"$sum": 1},
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    @staticmethod
    async def aggregate_top_doctors(
        collection: AsyncCollection[dict[str, Any]],
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> list[dict[str, Any]]:
        match_stage: dict[str, Any] = {
            "isDeleted": {"$ne": True},
            "createdAt": {"$gte": start_date, "$lte": end_date},
        }
        if branch_id:
            match_stage["branchId"] = branch_id

        pipeline = [
            {"$match": match_stage},
            {
                "$project": {
                    "branchId": 1,
                    "doctorId": 1,
                    "doctorName": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$doctorInfo.name", None]},
                                    {"$ne": ["$doctorInfo.name", ""]},
                                ]
                            },
                            "$doctorInfo.name",
                            "Sin Médico",
                        ]
                    },
                    "specialty": {
                        "$ifNull": ["$doctorInfo.specialty", ""]
                    },
                    "totalPrice": "$totalPrice",
                }
            },
            {
                "$group": {
                    "_id": {
                        "branchId": "$branchId",
                        "doctorId": "$doctorId",
                        "doctorName": "$doctorName",
                        "specialty": "$specialty",
                    },
                    "totalOrders": {"$sum": 1},
                    "totalRevenue": {"$sum": "$totalPrice"},
                }
            },
            {
                "$sort": {
                    "totalOrders": -1,
                    "totalRevenue": -1,
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    @staticmethod
    async def aggregate_orders_lab_tests(
        collection: AsyncCollection[dict[str, Any]],
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> list[dict[str, Any]]:
        match_stage: dict[str, Any] = {
            "isDeleted": {"$ne": True},
            "createdAt": {"$gte": start_date, "$lte": end_date},
        }
        if branch_id:
            match_stage["branchId"] = branch_id

        pipeline = [
            {"$match": match_stage},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": {
                        "branchId": "$branchId",
                        "labTestId": "$items.labTestId",
                        "name": "$items.name",
                        "isPack": {"$ifNull": ["$items.isPack", False]},
                    },
                    "timesOrdered": {"$sum": 1},
                    "totalRevenue": {
                        "$sum": {"$ifNull": ["$items.salePriceApplied", 0]}
                    },
                }
            },
            {
                "$sort": {
                    "timesOrdered": -1,
                    "totalRevenue": -1,
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    @staticmethod
    async def aggregate_quotations_lab_tests(
        collection: AsyncCollection[dict[str, Any]],
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> list[dict[str, Any]]:
        match_stage: dict[str, Any] = {
            "isDeleted": {"$ne": True},
            "createdAt": {"$gte": start_date, "$lte": end_date},
        }
        if branch_id:
            match_stage["branchId"] = branch_id

        pipeline = [
            {"$match": match_stage},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": {
                        "branchId": "$branchId",
                        "labTestId": "$items.labTestId",
                        "name": {
                            "$ifNull": ["$items.testName", "$items.name"]
                        },
                        "isPack": {"$ifNull": ["$items.isPack", False]},
                    },
                    "timesOrdered": {"$sum": 1},
                    "totalRevenue": {
                        "$sum": {"$ifNull": ["$items.price", 0]}
                    },
                }
            },
            {
                "$sort": {
                    "timesOrdered": -1,
                    "totalRevenue": -1,
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    @staticmethod
    async def aggregate_pending_balances(
        collection: AsyncCollection[dict[str, Any]],
        start_date: int,
        end_date: int,
        branch_id: str | None = None,
    ) -> list[dict[str, Any]]:
        match_stage: dict[str, Any] = {
            "isDeleted": {"$ne": True},
            "createdAt": {"$gte": start_date, "$lte": end_date},
            "$expr": {"$gt": ["$totalPrice", "$paidAmount"]},
        }
        if branch_id:
            match_stage["branchId"] = branch_id

        pipeline = [
            {"$match": match_stage},
            {
                "$project": {
                    "orderId": "$id",
                    "branchId": "$branchId",
                    "patientId": "$patientId",
                    "patientName": {
                        "$ifNull": ["$patientInfo.name", "Paciente"]
                    },
                    "patientPhone": {
                        "$ifNull": ["$patientInfo.phone", ""]
                    },
                    "totalPrice": "$totalPrice",
                    "paidAmount": "$paidAmount",
                    "pendingAmount": {
                        "$subtract": ["$totalPrice", "$paidAmount"]
                    },
                    "orderDate": "$createdAt",
                }
            },
            {"$sort": {"pendingAmount": -1}},
        ]

        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result
