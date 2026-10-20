from serum.core.counter_manager import CounterManager
from serum.tools.time_tools import TimeTools
from serum.tools.search_tools import generate_prefixes

from .data.patients_datasource import PatientsDataSource
from .models.patient_model import CreatePatient, PatientInDb, UpdatePatient


class PatientsRepository:
    _instance: "PatientsRepository|None" = None

    def __init__(self, patients_ds: PatientsDataSource):
        self.patients_ds = patients_ds

    @classmethod
    def get_instance(cls) -> "PatientsRepository":
        if cls._instance is None:
            cls._instance = cls(PatientsDataSource())
        return cls._instance

    async def create_patient(self, create_patient: CreatePatient) -> PatientInDb:
        patient_id = await CounterManager().next_patient_number()
        new_patient = PatientInDb(
            id=patient_id,
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            **create_patient.model_dump(),
        )
        new_patient_data = new_patient.model_dump()
        new_patient_data["searchPrefixes"] = generate_prefixes(new_patient.name)

        result = await self.patients_ds.create_patient(new_patient_data)

        return PatientInDb.model_validate(result)

    async def get_all_patients(
        self, origin_branch: str | None = None
    ) -> list[PatientInDb]:
        results = await self.patients_ds.get_all_patients(origin_branch=origin_branch)
        return [PatientInDb.model_validate(r) for r in results]

    async def get_patient_by_id(self, patient_id: str) -> PatientInDb | None:
        result = await self.patients_ds.get_patient_by_id(patient_id)
        if result is None:
            return None
        return PatientInDb.model_validate(result)

    async def get_patient_by_card_id(self, card_id: str) -> PatientInDb | None:
        result = await self.patients_ds.get_patient_by_card_id(card_id)
        if result is None:
            return None
        return PatientInDb.model_validate(result)

    async def search_patient_by_text(
        self, text_query: str, origin_branch: str | None = None
    ) -> list[PatientInDb]:
        results = await self.patients_ds.search_patient_by_text(
            text_query, origin_branch=origin_branch
        )
        return [PatientInDb.model_validate(r) for r in results]

    async def update_patient_by_id(
        self, patient_id: str, patient: UpdatePatient
    ) -> PatientInDb | None:
        updated_data = patient.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        if "name" in updated_data and updated_data["name"]:
            updated_data["searchPrefixes"] = generate_prefixes(updated_data["name"])

        result = await self.patients_ds.update_patient_by_id(patient_id, updated_data)
        if result is None:
            return None
        return PatientInDb.model_validate(result)

    async def delete_patient_by_id(self, patient_id: str) -> PatientInDb | None:
        result = await self.patients_ds.delete_patient_by_id(patient_id)
        if result is None:
            return None
        return PatientInDb.model_validate(result)
