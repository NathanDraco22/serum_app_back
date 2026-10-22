from fastapi import APIRouter, Depends, Request

from serum.repos.v1.common.filter_params import OrderFilterParams
from serum.repos.v1.orders import CreateOrder, OrderInDb, UpdateOrder
from responses.v1 import ListResponse

from .orders_controller import orders_controller
from .orders_schemas import OrderApproveRequest, OrderPayRequest

orders_router = APIRouter(tags=["ordersV1"])


@orders_router.post("")
async def create_order(body: CreateOrder) -> OrderInDb:
    return await orders_controller.create_order(body)


@orders_router.get("")
async def get_all_orders(
    query_params: OrderFilterParams = Depends(),
) -> ListResponse[OrderInDb]:
    return await orders_controller.get_all_orders(query_params)


@orders_router.get("/patient/{patient_id}")
async def get_orders_by_patient_id(
    patient_id: str,
    branch_id: str | None = None,
    all_branches: bool = True,
) -> ListResponse[OrderInDb]:
    return await orders_controller.get_orders_by_patient_id(
        patient_id=patient_id,
        branch_id=branch_id,
        all_branches=all_branches,
    )


@orders_router.get("/{order_id}")
async def get_order_by_id(order_id: str) -> OrderInDb:
    return await orders_controller.get_order_by_id(order_id)


@orders_router.patch("/{order_id}")
async def update_order_by_id(order_id: str, body: UpdateOrder) -> OrderInDb:
    return await orders_controller.update_order_by_id(order_id, body)


@orders_router.delete("/{order_id}")
async def delete_order_by_id(order_id: str) -> OrderInDb:
    return await orders_controller.delete_order_by_id(order_id)


@orders_router.post("/{order_id}/pay")
async def pay_order(order_id: str, body: OrderPayRequest) -> OrderInDb:
    return await orders_controller.pay_order(order_id, body)


@orders_router.post("/{order_id}/approve")
async def approve_order(
    order_id: str, body: OrderApproveRequest, req: Request
) -> OrderInDb:
    return await orders_controller.approve_order(order_id, body, req)
