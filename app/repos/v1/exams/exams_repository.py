from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool
from tools.search_tools import generate_prefixes

from .data.exams_datasource import ExamsDataSource
from .models.exam_model import CreateExam, ExamInDb, UpdateExam


class ExamsRepository:
    _instance: "ExamsRepository|None" = None

    def __init__(self, exams_ds: ExamsDataSource):
        self.exams_ds = exams_ds

    @classmethod
    def get_instance(cls) -> "ExamsRepository":
        if cls._instance is None:
            cls._instance = cls(ExamsDataSource())
        return cls._instance

    async def create_exam(self, create_exam: CreateExam) -> ExamInDb:
        new_exam = ExamInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_exam.model_dump(),
        )
        new_exam_data = new_exam.model_dump()
        new_exam_data["searchPrefixes"] = generate_prefixes(new_exam.name)

        result = await self.exams_ds.create_exam(new_exam_data)
        return ExamInDb.model_validate(result)

    async def get_all_exams(self) -> list[ExamInDb]:
        results = await self.exams_ds.get_all_exams()
        return [ExamInDb.model_validate(r) for r in results]

    async def get_exam_by_id(self, exam_id: str) -> ExamInDb | None:
        result = await self.exams_ds.get_exam_by_id(exam_id)
        if result is None:
            return None
        return ExamInDb.model_validate(result)

    async def search_exam_by_text(self, text_query: str) -> list[ExamInDb]:
        results = await self.exams_ds.search_exam_by_text(text_query)
        return [ExamInDb.model_validate(r) for r in results]

    async def update_exam_by_id(
        self, exam_id: str, exam: UpdateExam
    ) -> ExamInDb | None:
        updated_data = exam.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        if "name" in updated_data and updated_data["name"]:
            updated_data["searchPrefixes"] = generate_prefixes(updated_data["name"])

        result = await self.exams_ds.update_exam_by_id(exam_id, updated_data)
        if result is None:
            return None
        return ExamInDb.model_validate(result)

    async def delete_exam_by_id(self, exam_id: str) -> ExamInDb | None:
        result = await self.exams_ds.delete_exam_by_id(exam_id)
        if result is None:
            return None
        return ExamInDb.model_validate(result)
