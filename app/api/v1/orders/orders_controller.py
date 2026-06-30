from fastapi import HTTPException, status

from repos.v1.orders import (
    CreateOrder,
    UpdateOrder,
    OrderInDb,
    OrdersRepository,
)
from responses.v1 import ListResponse


class OrdersController:
    def __init__(self, orders_repo: OrdersRepository) -> None:
        self.orders_repo = orders_repo

    async def create_order(self, body: CreateOrder) -> OrderInDb:
        return await self.orders_repo.create_order(body)

    async def get_all_orders(self) -> ListResponse[OrderInDb]:
        orders = await self.orders_repo.get_all_orders()
        return ListResponse(count=len(orders), data=orders)

    async def get_order_by_id(self, order_id: str) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return order

    async def update_order_by_id(self, order_id: str, body: UpdateOrder) -> OrderInDb:
        updated_order = await self.orders_repo.update_order_by_id(order_id, body)
        if updated_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return updated_order

    async def delete_order_by_id(self, order_id: str) -> OrderInDb:
        deleted_order = await self.orders_repo.delete_order_by_id(order_id)
        if deleted_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return deleted_order


orders_controller = OrdersController(
    orders_repo=OrdersRepository.get_instance(),
)
