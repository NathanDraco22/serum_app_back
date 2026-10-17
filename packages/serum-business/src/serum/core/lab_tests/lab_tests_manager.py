from serum.repos.v1.lab_tests import CreateLabTest, LabTestInDb

from .process_create_lab_test import process_create_lab_test


class LabTestsManager:
    _instance: "LabTestsManager|None" = None

    @classmethod
    def get_instance(cls) -> "LabTestsManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_lab_test(self, create_data: CreateLabTest) -> LabTestInDb:
        return await process_create_lab_test(create_data)
