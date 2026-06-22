from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool

from .data.doctors_datasource import DoctorsDataSource
from .models.doctor_model import CreateDoctor, UpdateDoctor, DoctorInDb


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
        new_doctor = DoctorInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
            **create_doctor.model_dump(),
        )
        result = await self.doctors_ds.create_doctor(new_doctor.model_dump())
        return DoctorInDb.model_validate(result)

    async def get_all_doctors(self) -> list[DoctorInDb]:
        results = await self.doctors_ds.get_all_doctors()
        return [DoctorInDb.model_validate(r) for r in results]

    async def get_doctor_by_id(self, doctor_id: str) -> DoctorInDb | None:
        result = await self.doctors_ds.get_doctor_by_id(doctor_id)
        if result is None:
            return None
        return DoctorInDb.model_validate(result)

    async def update_doctor_by_id(self, doctor_id: str, doctor: UpdateDoctor) -> DoctorInDb | None:
        updated_data = doctor.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.doctors_ds.update_doctor_by_id(doctor_id, updated_data)
        if result is None:
            return None
        return DoctorInDb.model_validate(result)

    async def delete_doctor_by_id(self, doctor_id: str) -> DoctorInDb | None:
        result = await self.doctors_ds.delete_doctor_by_id(doctor_id)
        if result is None:
            return None
        return DoctorInDb.model_validate(result)
