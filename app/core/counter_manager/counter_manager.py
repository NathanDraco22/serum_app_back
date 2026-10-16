from typing import Any
from repos.v1.counters import CountersRepository


class CounterManager:
    _instance: "CounterManager | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CounterManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.counters_repository = CountersRepository.get_instance()

    async def next_patient_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter("patientNumber", session)
        return str(res.value).zfill(4)

    async def set_patient_number(self, number: int, session: Any = None) -> str:
        res = await self.counters_repository.set_counter(
            "patientNumber", number, session
        )
        return str(res.value).zfill(4)

    async def next_doctor_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter("doctorNumber", session)
        return str(res.value).zfill(4)

    async def set_doctor_number(self, number: int, session: Any = None) -> str:
        res = await self.counters_repository.set_counter(
            "doctorNumber", number, session
        )
        return str(res.value).zfill(4)

    async def next_order_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter("orderNumber", session)
        return str(res.value)

    async def set_order_number(self, number: int, session: Any = None) -> str:
        res = await self.counters_repository.set_counter(
            "orderNumber", number, session
        )
        return str(res.value)

    async def next_quotation_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter(
            "quotationNumber", session
        )
        return str(res.value)

    async def set_quotation_number(self, number: int, session: Any = None) -> str:
        res = await self.counters_repository.set_counter(
            "quotationNumber", number, session
        )
        return str(res.value)

    async def next_shift_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter(
            "shiftNumber", session
        )
        return str(res.value)

    async def set_shift_number(self, number: int, session: Any = None) -> str:
        res = await self.counters_repository.set_counter(
            "shiftNumber", number, session
        )
        return str(res.value)

    async def next_branch_number(self, session: Any = None) -> str:
        counter = await self.counters_repository.get_counter("branchNumber")
        if counter is None:
            await self.counters_repository.set_counter("branchNumber", 1, session)
        res = await self.counters_repository.increment_counter(
            "branchNumber", session
        )
        return f"BR{res.value}"

    async def set_branch_number(self, number: int, session: Any = None) -> str:
        res = await self.counters_repository.set_counter(
            "branchNumber", number, session
        )
        return f"BR{res.value}"

    async def next_receipt_number(self, session: Any = None) -> str:
        res = await self.counters_repository.increment_counter(
            "receiptNumber", session
        )
        return str(res.value)

    async def set_receipt_number(self, number: int, session: Any = None) -> str:
        res = await self.counters_repository.set_counter(
            "receiptNumber", number, session
        )
        return str(res.value)


