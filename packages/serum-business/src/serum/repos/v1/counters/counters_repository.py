from typing import Any

from .data.counters_datasource import CountersDataSource
from .models.counter_model import CounterInDb


class CountersRepository:
    _instance: "CountersRepository | None" = None

    def __init__(self, counters_ds: CountersDataSource):
        self.counters_ds = counters_ds

    @classmethod
    def get_instance(cls) -> "CountersRepository":
        if cls._instance is None:
            cls._instance = cls(counters_ds=CountersDataSource())
        return cls._instance

    async def increment_counter(
        self, counter_name: str, session: Any = None
    ) -> CounterInDb:
        result = await self.counters_ds.increment_counter(counter_name, session)
        return CounterInDb.model_validate(result)

    async def set_counter(
        self, counter_name: str, value: int, session: Any = None
    ) -> CounterInDb:
        result = await self.counters_ds.set_counter(counter_name, value, session)
        return CounterInDb.model_validate(result)

    async def get_counter(self, counter_name: str) -> CounterInDb | None:
        result = await self.counters_ds.get_counter(counter_name)
        if result is None:
            return None
        return CounterInDb.model_validate(result)
