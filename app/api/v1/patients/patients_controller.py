from fastapi import HTTPException, status
from serum.serum_config import serumCtx

from serum.repos.v1.patients import (
    CreatePatient,
    PatientInDb,
    PatientsRepository,
    UpdatePatient,
)
from responses.v1 import ListResponse


class PatientsController:
    def __init__(self, patients_repo: PatientsRepository) -> None:
        self.patients_repo = patients_repo

    async def create_patient(self, body: CreatePatient) -> PatientInDb:
        if body.cardId is not None and body.cardId != "":
            res = await self.patients_repo.get_patient_by_card_id(body.cardId)
            if res is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Esta cedula fue registrada: {res.name}",
                )
        return await self.patients_repo.create_patient(body)

    async def get_all_patients(
        self, origin_branch: str | None = None
    ) -> ListResponse[PatientInDb]:
        effective_branch = origin_branch or serumCtx.get().branchId or None
        patients = await self.patients_repo.get_all_patients(
            origin_branch=effective_branch
        )
        return ListResponse(count=len(patients), data=patients)

    async def search_patient_by_text(
        self, text_query: str, origin_branch: str | None = None
    ) -> ListResponse[PatientInDb]:
        effective_branch = origin_branch or serumCtx.get().branchId or None
        patients = await self.patients_repo.search_patient_by_text(
            text_query, origin_branch=effective_branch
        )
        return ListResponse(count=len(patients), data=patients)

    async def get_patient_by_id(self, patient_id: str) -> PatientInDb:
        patient = await self.patients_repo.get_patient_by_id(patient_id)
        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )
        return patient

    async def update_patient_by_id(
        self, patient_id: str, body: UpdatePatient
    ) -> PatientInDb:
        updated_patient = await self.patients_repo.update_patient_by_id(
            patient_id, body
        )
        if updated_patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )
        return updated_patient

    async def delete_patient_by_id(self, patient_id: str) -> PatientInDb:
        deleted_patient = await self.patients_repo.delete_patient_by_id(patient_id)
        if deleted_patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )
        return deleted_patient


patients_controller = PatientsController(
    patients_repo=PatientsRepository.get_instance(),
)
