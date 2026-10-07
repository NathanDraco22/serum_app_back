from typing import Any
from services.mongo_collections.v1 import CountersCollection


class CountersDataSource:
    async def increment_counter(
        self, counter_name: str, session: Any = None
    ) -> dict[str, Any]:
        return await CountersCollection.get_instance().increment_counter(
            counter_name, session
        )

    async def set_counter(
        self, counter_name: str, value: int, session: Any = None
    ) -> dict[str, Any]:
        return await CountersCollection.get_instance().set_counter(
            counter_name, value, session
        )

    async def get_counter(self, counter_name: str) -> dict[str, Any] | None:
        return await CountersCollection.get_instance().get_counter(counter_name)
