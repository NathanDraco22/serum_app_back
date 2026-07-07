from typing import Any

from services.mongo_collections.v1 import ExamsCollection


class ExamsDataSource:
    async def create_exam(self, exam: dict[str, Any]) -> dict[str, Any]:
        collection = ExamsCollection.get_instance()
        await collection.create_exam(exam)
        return exam

    async def get_all_exams(self) -> list[dict[str, Any]]:
        collection = ExamsCollection.get_instance()
        return await collection.fetch_all_exams()

    async def get_exam_by_id(self, exam_id: str) -> dict[str, Any] | None:
        collection = ExamsCollection.get_instance()
        return await collection.fetch_exam_by_id(exam_id)

    async def update_exam_by_id(
        self, exam_id: str, exam: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ExamsCollection.get_instance()
        return await collection.update_exam_by_id(exam_id, exam)

    async def delete_exam_by_id(self, exam_id: str) -> dict[str, Any] | None:
        collection = ExamsCollection.get_instance()
        return await collection.delete_exam_by_id(exam_id)
