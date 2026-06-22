from fastapi import APIRouter

from repos.v1.patients import CreatePatient, UpdatePatient, PatientInDb
from responses.v1 import ListResponse

from .patients_controller import patients_controller


patients_router = APIRouter(tags=["patientsV1"])


@patients_router.post("")
async def create_patient(body: CreatePatient) -> PatientInDb:
    return await patients_controller.create_patient(body)


@patients_router.get("")
async def get_all_patients() -> ListResponse[PatientInDb]:
    return await patients_controller.get_all_patients()


@patients_router.get("/{patient_id}")
async def get_patient_by_id(patient_id: str) -> PatientInDb:
    return await patients_controller.get_patient_by_id(patient_id)


@patients_router.patch("/{patient_id}")
async def update_patient_by_id(patient_id: str, body: UpdatePatient) -> PatientInDb: 
    return await patients_controller.update_patient_by_id(patient_id, body)


@patients_router.delete("/{patient_id}")
async def delete_patient_by_id(patient_id: str) -> PatientInDb:
    return await patients_controller.delete_patient_by_id(patient_id)
