from fastapi import HTTPException, status

from repos.v1.patients import (
    CreatePatient, 
    UpdatePatient, 
    PatientInDb, 
    PatientsRepository,
)
from responses.v1 import ListResponse


class PatientsController:
    def __init__(self, patients_repo: PatientsRepository) -> None:
        self.patients_repo = patients_repo

    async def create_patient(self, body: CreatePatient) -> PatientInDb:
        return await self.patients_repo.create_patient(body)

    async def get_all_patients(self) -> ListResponse[PatientInDb]:
        patients = await self.patients_repo.get_all_patients()
        return ListResponse(count=len(patients), data=patients)

    async def get_patient_by_id(self, patient_id: str) -> PatientInDb:
        patient = await self.patients_repo.get_patient_by_id(patient_id)
        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found",
            )
        return patient

    async def update_patient_by_id(self, patient_id: str, body: UpdatePatient) -> PatientInDb:
        updated_patient = await self.patients_repo.update_patient_by_id(patient_id, body)
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
