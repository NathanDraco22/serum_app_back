from fastapi import HTTPException, status

from repos.v1.common.filter_params import OrderFilterParams
from repos.v1.orders import (
    CreateOrder,
    OrderInDb,
    OrdersRepository,
    UpdateOrder,
)
from core.order_payment.order_payment import OrderPayIntent
from core.order_payment.order_payment_manager import OrderPaymentManager
from core.exceptions import OrderAlreadyPaid, OrderCannotBeDeleted, OrderNotFound
from responses.v1 import ListResponse
from .orders_schemas import OrderPayRequest


class OrdersController:
    def __init__(self, orders_repo: OrdersRepository) -> None:
        self.orders_repo = orders_repo
        self.order_payment_manager = OrderPaymentManager()

    async def create_order(self, body: CreateOrder) -> OrderInDb:
        return await self.orders_repo.create_order(body)

    async def get_all_orders(
        self, query_params: OrderFilterParams | None = None
    ) -> ListResponse[OrderInDb]:
        orders = await self.orders_repo.get_all_orders(query_params)
        return ListResponse(count=len(orders), data=orders)

    async def get_order_by_id(self, order_id: str) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return order

    async def pay_order(self, order_id: str, body: OrderPayRequest) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        pay_intent = OrderPayIntent(
            orderId=order_id,
            amount=body.amount,
            shiftId=body.shiftId,
            registerId=body.registerId,
            paymentMethod=body.paymentMethod,
            performedBy=body.performedBy,
        )

        try:
            return await self.order_payment_manager.pay_order(pay_intent)
        except OrderAlreadyPaid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot receive payments",
            )
        except OrderNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

    async def update_order_by_id(self, order_id: str, body: UpdateOrder) -> OrderInDb:
        updated_order = await self.orders_repo.update_order_by_id(order_id, body)
        if updated_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return updated_order

    async def delete_order_by_id(self, order_id: str) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        if order.status != "pending" or order.paidAmount > 0:
            raise OrderCannotBeDeleted()

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
