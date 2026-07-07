from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool

from .data.orders_datasource import OrdersDataSource
from .models.order_model import CreateOrder, OrderInDb, UpdateOrder


class OrdersRepository:
    _instance: "OrdersRepository|None" = None

    def __init__(self, orders_ds: OrdersDataSource):
        self.orders_ds = orders_ds

    @classmethod
    def get_instance(cls) -> "OrdersRepository":
        if cls._instance is None:
            cls._instance = cls(OrdersDataSource())
        return cls._instance

    async def create_order(self, create_order: CreateOrder) -> OrderInDb:
        new_order = OrderInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_order.model_dump(),
        )
        result = await self.orders_ds.create_order(new_order.model_dump())
        return OrderInDb.model_validate(result)

    async def get_all_orders(self) -> list[OrderInDb]:
        results = await self.orders_ds.get_all_orders()
        return [OrderInDb.model_validate(r) for r in results]

    async def get_order_by_id(self, order_id: str) -> OrderInDb | None:
        result = await self.orders_ds.get_order_by_id(order_id)
        if result is None:
            return None
        return OrderInDb.model_validate(result)

    async def update_order_by_id(
        self, order_id: str, order: UpdateOrder
    ) -> OrderInDb | None:
        updated_data = order.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.orders_ds.update_order_by_id(order_id, updated_data)
        if result is None:
            return None
        return OrderInDb.model_validate(result)

    async def delete_order_by_id(self, order_id: str) -> OrderInDb | None:
        result = await self.orders_ds.delete_order_by_id(order_id)
        if result is None:
            return None
        return OrderInDb.model_validate(result)
