from serum.core.counter_manager import CounterManager
from serum.tools.time_tools import TimeTools
from serum.tools.search_tools import generate_prefixes

from .data.doctors_datasource import DoctorsDataSource
from .models.doctor_model import CreateDoctor, DoctorInDb, UpdateDoctor


class DoctorsRepository:
    _instance: "DoctorsRepository|None" = None

    def __init__(self, doctors_ds: DoctorsDataSource):
        self.doctors_ds = doctors_ds

    @classmethod
    def get_instance(cls) -> "DoctorsRepository":
        if cls._instance is None:
            cls._instance = cls(DoctorsDataSource())
        return cls._instance

    async def create_doctor(self, create_doctor: CreateDoctor) -> DoctorInDb:
        doctor_id = await CounterManager().next_doctor_number()
        new_doctor = DoctorInDb(
            id=doctor_id,
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            **create_doctor.model_dump(),
        )
        new_doctor_data = new_doctor.model_dump()
        new_doctor_data["searchPrefixes"] = generate_prefixes(new_doctor.name)

        result = await self.doctors_ds.create_doctor(new_doctor_data)

        return DoctorInDb.model_validate(result)

    async def get_all_doctors(self) -> list[DoctorInDb]:
        results = await self.doctors_ds.get_all_doctors()
        return [DoctorInDb.model_validate(r) for r in results]

    async def get_doctor_by_id(self, doctor_id: str) -> DoctorInDb | None:
        result = await self.doctors_ds.get_doctor_by_id(doctor_id)
        if result is None:
            return None
        return DoctorInDb.model_validate(result)

    async def get_doctor_by_card_id(self, card_id: str) -> DoctorInDb | None:
        result = await self.doctors_ds.get_doctor_by_card_id(card_id)
        if result is None:
            return None
        return DoctorInDb.model_validate(result)

    async def search_doctor_by_text(self, text_query: str) -> list[DoctorInDb]:
        results = await self.doctors_ds.search_doctor_by_text(text_query)
        return [DoctorInDb.model_validate(r) for r in results]

    async def update_doctor_by_id(
        self, doctor_id: str, doctor: UpdateDoctor
    ) -> DoctorInDb | None:
        updated_data = doctor.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        if "name" in updated_data and updated_data["name"]:
            updated_data["searchPrefixes"] = generate_prefixes(updated_data["name"])

        result = await self.doctors_ds.update_doctor_by_id(doctor_id, updated_data)
        if result is None:
            return None
        return DoctorInDb.model_validate(result)

    async def delete_doctor_by_id(self, doctor_id: str) -> DoctorInDb | None:
        result = await self.doctors_ds.delete_doctor_by_id(doctor_id)
        if result is None:
            return None
        return DoctorInDb.model_validate(result)
