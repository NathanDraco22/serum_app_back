from fastapi import APIRouter

from repos.v1.doctors import CreateDoctor, UpdateDoctor, DoctorInDb
from responses.v1 import ListResponse

from .doctors_controller import doctors_controller


doctors_router = APIRouter(tags=["doctorsV1"])


@doctors_router.post("")
async def create_doctor(body: CreateDoctor) -> DoctorInDb:
    return await doctors_controller.create_doctor(body)


@doctors_router.get("")
async def get_all_doctors() -> ListResponse[DoctorInDb]:
    return await doctors_controller.get_all_doctors()


@doctors_router.get("/{doctor_id}")
async def get_doctor_by_id(doctor_id: str) -> DoctorInDb:
    return await doctors_controller.get_doctor_by_id(doctor_id)


@doctors_router.patch("/{doctor_id}")
async def update_doctor_by_id(doctor_id: str, body: UpdateDoctor) -> DoctorInDb: 
    return await doctors_controller.update_doctor_by_id(doctor_id, body)


@doctors_router.delete("/{doctor_id}")
async def delete_doctor_by_id(doctor_id: str) -> DoctorInDb:
    return await doctors_controller.delete_doctor_by_id(doctor_id)
