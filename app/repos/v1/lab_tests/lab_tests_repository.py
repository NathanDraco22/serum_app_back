from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool
from tools.search_tools import generate_prefixes

from .data.lab_tests_datasource import LabTestsDataSource
from .models.lab_test_model import CreateLabTest, LabTestInDb, UpdateLabTest


class LabTestsRepository:
    _instance: "LabTestsRepository|None" = None

    def __init__(self, lab_tests_ds: LabTestsDataSource):
        self.lab_tests_ds = lab_tests_ds

    @classmethod
    def get_instance(cls) -> "LabTestsRepository":
        if cls._instance is None:
            cls._instance = cls(LabTestsDataSource())
        return cls._instance

    async def create_lab_test(self, create_lab_test: CreateLabTest) -> LabTestInDb:
        new_lab_test = LabTestInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_lab_test.model_dump(),
        )
        new_lab_test_data = new_lab_test.model_dump()
        new_lab_test_data["searchPrefixes"] = generate_prefixes(new_lab_test.name)

        result = await self.lab_tests_ds.create_lab_test(new_lab_test_data)
        return LabTestInDb.model_validate(result)

    async def get_all_lab_tests(self) -> list[LabTestInDb]:
        results = await self.lab_tests_ds.get_all_lab_tests()
        return [LabTestInDb.model_validate(r) for r in results]

    async def get_lab_test_by_id(self, lab_test_id: str) -> LabTestInDb | None:
        result = await self.lab_tests_ds.get_lab_test_by_id(lab_test_id)
        if result is None:
            return None
        return LabTestInDb.model_validate(result)

    async def search_lab_test_by_text(self, text_query: str) -> list[LabTestInDb]:
        results = await self.lab_tests_ds.search_lab_test_by_text(text_query)
        return [LabTestInDb.model_validate(r) for r in results]

    async def update_lab_test_by_id(
        self, lab_test_id: str, lab_test: UpdateLabTest
    ) -> LabTestInDb | None:
        updated_data = lab_test.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        if "name" in updated_data and updated_data["name"]:
            updated_data["searchPrefixes"] = generate_prefixes(updated_data["name"])

        result = await self.lab_tests_ds.update_lab_test_by_id(
            lab_test_id, updated_data
        )
        if result is None:
            return None
        return LabTestInDb.model_validate(result)

    async def delete_lab_test_by_id(self, lab_test_id: str) -> LabTestInDb | None:
        result = await self.lab_tests_ds.delete_lab_test_by_id(lab_test_id)
        if result is None:
            return None
        return LabTestInDb.model_validate(result)
