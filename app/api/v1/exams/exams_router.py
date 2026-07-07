from fastapi import APIRouter

from repos.v1.exams import CreateExam, ExamInDb, UpdateExam
from responses.v1 import ListResponse

from .exams_controller import exams_controller

exams_router = APIRouter(tags=["examsV1"])


@exams_router.post("")
async def create_exam(body: CreateExam) -> ExamInDb:
    return await exams_controller.create_exam(body)


@exams_router.get("")
async def get_all_exams() -> ListResponse[ExamInDb]:
    return await exams_controller.get_all_exams()


@exams_router.get("/{exam_id}")
async def get_exam_by_id(exam_id: str) -> ExamInDb:
    return await exams_controller.get_exam_by_id(exam_id)


@exams_router.patch("/{exam_id}")
async def update_exam_by_id(exam_id: str, body: UpdateExam) -> ExamInDb:
    return await exams_controller.update_exam_by_id(exam_id, body)


@exams_router.delete("/{exam_id}")
async def delete_exam_by_id(exam_id: str) -> ExamInDb:
    return await exams_controller.delete_exam_by_id(exam_id)
