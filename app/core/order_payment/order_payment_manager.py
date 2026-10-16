import asyncio

from pymongo.errors import OperationFailure

from repos.v1.orders import OrderInDb, OrdersRepository
from core.exceptions import OrderNotFound, OrderAlreadyPaid, OrderIsBlocked

from .order_payment import OrderPayIntent
from .process_order_payment import process_order_payment


class OrderPaymentManager:
    def __init__(self) -> None:
        self.orders_repo = OrdersRepository.get_instance()

    async def pay_order(self, pay_intent: OrderPayIntent) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(pay_intent.orderId)
        if order is None:
            raise OrderNotFound()
        if order.isBlocked:
            raise OrderIsBlocked()
        if order.status not in ("pending", "partiallyPaid", "completed") or (
            order.totalPrice > 0 and order.paidAmount >= order.totalPrice
        ):
            raise OrderAlreadyPaid()

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_order_payment(pay_intent=pay_intent)
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise

        raise RuntimeError("Server is too busy, try again later")
