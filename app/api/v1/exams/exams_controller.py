from fastapi import HTTPException, status

from repos.v1.exams import (
    CreateExam,
    ExamInDb,
    ExamsRepository,
    UpdateExam,
)
from responses.v1 import ListResponse


class ExamsController:
    def __init__(self, exams_repo: ExamsRepository) -> None:
        self.exams_repo = exams_repo

    async def create_exam(self, body: CreateExam) -> ExamInDb:
        return await self.exams_repo.create_exam(body)

    async def get_all_exams(self) -> ListResponse[ExamInDb]:
        exams = await self.exams_repo.get_all_exams()
        return ListResponse(count=len(exams), data=exams)

    async def get_exam_by_id(self, exam_id: str) -> ExamInDb:
        exam = await self.exams_repo.get_exam_by_id(exam_id)
        if exam is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found",
            )
        return exam

    async def update_exam_by_id(self, exam_id: str, body: UpdateExam) -> ExamInDb:
        updated_exam = await self.exams_repo.update_exam_by_id(exam_id, body)
        if updated_exam is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found",
            )
        return updated_exam

    async def delete_exam_by_id(self, exam_id: str) -> ExamInDb:
        deleted_exam = await self.exams_repo.delete_exam_by_id(exam_id)
        if deleted_exam is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found",
            )
        return deleted_exam


exams_controller = ExamsController(
    exams_repo=ExamsRepository.get_instance(),
)
