import re
from typing import Any

from pymongo import ReturnDocument, IndexModel

from serum.services import BaseMongoCollection


class LabTestsCollection(BaseMongoCollection):
    collection_name = "LabTests"

    @staticmethod
    def _get_branch_account_lookup_stages(branchId: str) -> list[dict[str, Any]]:
        return [
            {
                "$lookup": {
                    "from": "LabTestAccounts",
                    "let": {"testId": "$id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$labTestId", "$$testId"]},
                                        {"$eq": ["$branchId", branchId]},
                                        {"$eq": ["$isDeleted", False]},
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "_accountDocs",
                }
            },
            {
                "$addFields": {
                    "_account": {"$arrayElemAt": ["$_accountDocs", 0]},
                }
            },
            {
                "$addFields": {
                    "commercial": {
                        "$ifNull": [
                            "$_account.commercial",
                            {
                                "salePrice": "$salePrice",
                                "salePrice2": "$salePrice2",
                                "costPrice": 0,
                                "currency": "$currency",
                            },
                        ]
                    },
                    "salePrice": {
                        "$ifNull": ["$_account.commercial.salePrice", "$salePrice"]
                    },
                    "salePrice2": {
                        "$ifNull": ["$_account.commercial.salePrice2", "$salePrice2"]
                    },
                    "costPrice": {
                        "$ifNull": ["$_account.commercial.costPrice", 0]
                    },
                }
            },
            {
                "$project": {
                    "_accountDocs": 0,
                    "_account": 0,
                }
            },
        ]

    async def create_lab_test(self, lab_test: dict, session: Any = None) -> None:
        collection = self._collection
        await collection.insert_one(lab_test, session=session)

    async def create_lab_tests_batch(
        self, lab_tests: list[dict[str, Any]], session: Any = None
    ) -> None:
        if not lab_tests:
            return
        collection = self._collection
        await collection.insert_many(lab_tests, session=session)

    async def fetch_all_lab_tests(
        self, branchId: str | None = None, branch_id: str | None = None
    ) -> list[dict[str, Any]]:
        effective_branch = branchId or branch_id
        collection = self._collection
        if effective_branch:
            pipeline = [
                {"$match": {"isDeleted": False}},
                *self._get_branch_account_lookup_stages(effective_branch),
            ]
            cursor = await collection.aggregate(pipeline)
        else:
            cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_lab_test_by_id(
        self, lab_test_id: str, branchId: str | None = None, branch_id: str | None = None
    ) -> dict[str, Any] | None:
        effective_branch = branchId or branch_id
        collection = self._collection
        if effective_branch:
            pipeline = [
                {"$match": {"id": lab_test_id, "isDeleted": False}},
                *self._get_branch_account_lookup_stages(effective_branch),
            ]
            cursor = await collection.aggregate(pipeline)
            results = await cursor.to_list(length=1)
            await cursor.close()
            return results[0] if results else None

        result = await collection.find_one({"id": lab_test_id, "isDeleted": False})
        return result

    async def search_lab_test_by_text(
        self, text_query: str, branchId: str | None = None, branch_id: str | None = None
    ) -> list[dict[str, Any]]:
        effective_branch = branchId or branch_id
        collection = self._collection
        safe_query = re.escape(text_query)

        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "$text": {
                        "$search": safe_query,
                        "$caseSensitive": False,
                        "$diacriticSensitive": False,
                    },
                    "isDeleted": False,
                }
            },
            {
                "$addFields": {
                    "baseScore": {"$meta": "textScore"},
                    "positionBoost": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": "$name",
                                    "regex": f"^{safe_query}",
                                    "options": "i",
                                }
                            },
                            100,
                            0,
                        ]
                    },
                }
            },
            {"$addFields": {"finalScore": {"$add": ["$baseScore", "$positionBoost"]}}},
            {"$sort": {"finalScore": -1, "name": 1}},
            {"$limit": 20},
        ]

        if effective_branch:
            pipeline.extend(self._get_branch_account_lookup_stages(effective_branch))

        pipeline.append(
            {"$project": {"baseScore": 0, "positionBoost": 0, "finalScore": 0}}
        )

        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def update_lab_test_by_id(
        self,
        lab_test_id: str,
        lab_test: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": lab_test_id, "isDeleted": False},
            {"$set": lab_test},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_lab_test_by_id(self, lab_test_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": lab_test_id, "isDeleted": False},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def create_indexes(self):
        from pymongo.errors import OperationFailure

        collection = self._collection
        indexes = [
            IndexModel(
                [
                    ("id", 1),
                ],
                unique=True,
            ),
            IndexModel(
                [
                    ("name", "text"),
                    ("code", "text"),
                    ("searchPrefixes", "text"),
                    ("commercialCategory", "text"),
                    ("id", "text"),
                ],
                weights={
                    "name": 10,
                    "code": 8,
                    "searchPrefixes": 5,
                    "commercialCategory": 3,
                    "id": 1,
                },
                name="TextSearchIndex",
            ),
        ]
        try:
            await collection.create_indexes(indexes)
        except OperationFailure as e:
            if e.code in (85, 86):
                try:
                    await collection.drop_index("TextSearchIndex")
                except Exception:
                    pass
                await collection.create_indexes(indexes)
            else:
                raise
