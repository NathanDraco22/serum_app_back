from fastapi import HTTPException, status

from serum.repos.v1.doctors import (
    CreateDoctor,
    DoctorInDb,
    DoctorsRepository,
    UpdateDoctor,
)
from responses.v1 import ListResponse


class DoctorsController:
    def __init__(self, doctors_repo: DoctorsRepository) -> None:
        self.doctors_repo = doctors_repo

    async def create_doctor(self, body: CreateDoctor) -> DoctorInDb:
        if body.cardId is not None and body.cardId != "":
            res = await self.doctors_repo.get_doctor_by_card_id(body.cardId)
            if res is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Esta cedula fue registrada: {res.name}",
                )
        return await self.doctors_repo.create_doctor(body)

    async def get_all_doctors(self) -> ListResponse[DoctorInDb]:
        doctors = await self.doctors_repo.get_all_doctors()
        return ListResponse(count=len(doctors), data=doctors)

    async def search_doctor_by_text(self, text_query: str) -> ListResponse[DoctorInDb]:
        doctors = await self.doctors_repo.search_doctor_by_text(text_query)
        return ListResponse(count=len(doctors), data=doctors)

    async def get_doctor_by_id(self, doctor_id: str) -> DoctorInDb:
        doctor = await self.doctors_repo.get_doctor_by_id(doctor_id)
        if doctor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )
        return doctor

    async def update_doctor_by_id(
        self, doctor_id: str, body: UpdateDoctor
    ) -> DoctorInDb:
        updated_doctor = await self.doctors_repo.update_doctor_by_id(doctor_id, body)
        if updated_doctor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )
        return updated_doctor

    async def delete_doctor_by_id(self, doctor_id: str) -> DoctorInDb:
        deleted_doctor = await self.doctors_repo.delete_doctor_by_id(doctor_id)
        if deleted_doctor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Doctor not found",
            )
        return deleted_doctor


doctors_controller = DoctorsController(
    doctors_repo=DoctorsRepository.get_instance(),
)
