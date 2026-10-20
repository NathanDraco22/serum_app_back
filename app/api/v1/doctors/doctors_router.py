from fastapi import APIRouter, Query

from serum.repos.v1.doctors import CreateDoctor, DoctorInDb, UpdateDoctor
from responses.v1 import ListResponse

from .doctors_controller import doctors_controller

doctors_router = APIRouter(tags=["doctorsV1"])


@doctors_router.post("")
async def create_doctor(body: CreateDoctor) -> DoctorInDb:
    return await doctors_controller.create_doctor(body)


@doctors_router.get("")
async def get_all_doctors(
    origin_branch: str | None = Query(None),
) -> ListResponse[DoctorInDb]:
    return await doctors_controller.get_all_doctors(origin_branch=origin_branch)


@doctors_router.get("/search/{text_query}")
async def search_doctor_by_text(
    text_query: str,
    origin_branch: str | None = Query(None),
) -> ListResponse[DoctorInDb]:
    return await doctors_controller.search_doctor_by_text(
        text_query, origin_branch=origin_branch
    )


@doctors_router.get("/{doctor_id}")
async def get_doctor_by_id(doctor_id: str) -> DoctorInDb:
    return await doctors_controller.get_doctor_by_id(doctor_id)


@doctors_router.patch("/{doctor_id}")
async def update_doctor_by_id(doctor_id: str, body: UpdateDoctor) -> DoctorInDb:
    return await doctors_controller.update_doctor_by_id(doctor_id, body)


@doctors_router.delete("/{doctor_id}")
async def delete_doctor_by_id(doctor_id: str) -> DoctorInDb:
    return await doctors_controller.delete_doctor_by_id(doctor_id)
