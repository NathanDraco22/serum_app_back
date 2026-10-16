from fastapi import HTTPException, Request, status

from core.exceptions import OrderCannotBeDeleted, OrderIsBlocked
from core.order_payment.order_payment import OrderPayIntent
from core.order_payment.order_payment_manager import OrderPaymentManager
from core.security import SysPasswordHasher, TokenManager
from repos.v1.common.filter_params import OrderFilterParams
from repos.v1.common.models.user_info import UserInfo
from repos.v1.orders import (
    CreateOrder,
    OrderApproval,
    OrderInDb,
    OrdersRepository,
    UpdateOrder,
)
from repos.v1.users import UsersRepository
from responses.v1 import ListResponse
from tools.time_tools import TimeTools

from .orders_schemas import OrderApproveRequest, OrderPayRequest


class OrdersController:
    def __init__(self, orders_repo: OrdersRepository) -> None:
        self.orders_repo = orders_repo
        self.order_payment_manager = OrderPaymentManager()
        self.users_repo = UsersRepository.get_instance()

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
        pay_intent = OrderPayIntent(
            orderId=order_id,
            amount=body.amount,
            shiftId=body.shiftId,
            registerId=body.registerId,
            paymentMethod=body.paymentMethod,
            performedBy=body.performedBy,
        )
        return await self.order_payment_manager.pay_order(pay_intent)

    async def update_order_by_id(self, order_id: str, body: UpdateOrder) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        # No permitir capturar ni alterar resultados si la orden se encuentra bloqueada
        if order.isBlocked and body.results is not None:
            raise OrderIsBlocked()

        updated_order = await self.orders_repo.update_order_by_id(order_id, body)
        if updated_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return updated_order

    async def approve_order(
        self, order_id: str, body: OrderApproveRequest, req: Request
    ) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        approver: UserInfo | None = None

        # Opción A: Credenciales explícitas de supervisor (desbloqueo en ventanilla)
        if body.supervisorUsername and body.supervisorPassword:
            sup_user = await self.users_repo.get_user_by_username(
                body.supervisorUsername
            )
            if sup_user is None:
                sup_user = await self.users_repo.get_user_by_email(
                    body.supervisorUsername
                )
            if sup_user is None:
                sup_user = await self.users_repo.get_user_by_phone(
                    body.supervisorUsername
                )

            if (
                sup_user is None
                or not sup_user.isActive
                or sup_user.isDeleted
                or not SysPasswordHasher.verify_password(
                    body.supervisorPassword, sup_user.password
                )
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales de supervisor incorrectas",
                )

            if sup_user.accessLevel <= 3:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="El usuario no tiene nivel de acceso suficiente (> 3) para autorizar",
                )

            approver = UserInfo(id=sup_user.id, name=sup_user.name)

        # Opción B: Usuario autenticado en sesión con nivel > 3
        if approver is None:
            auth_header = req.headers.get("Authorization") or req.headers.get(
                "authorization"
            )
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "").strip()
                payload = TokenManager.decode_token(token)
                if payload:
                    access_level = payload.get("accessLevel", 0)
                    user_id = payload.get("userId")
                    if access_level > 3 and user_id:
                        user = await self.users_repo.get_user_by_id(user_id)
                        name = user.name if user else payload.get("username", "Supervisor")
                        approver = UserInfo(id=user_id, name=name)

        # Opción C: approvedBy proporcionado directamente si se validó previamente
        if approver is None and body.approvedBy:
            approver = body.approvedBy

        if approver is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requiere autorización de un usuario con nivel de acceso mayor a 3",
            )

        update_data = UpdateOrder(
            isBlocked=False,
            approval=OrderApproval(
                requiresApproval=True,
                isApproved=True,
                approvedBy=approver,
                approvedAt=TimeTools.get_now_in_milliseconds(),
                reason=body.reason or "Aprobado por supervisor",
            ),
        )

        updated = await self.orders_repo.update_order_by_id(order_id, update_data)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return updated

    async def delete_order_by_id(self, order_id: str) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        # Una orden bloqueada o pendiente puede eliminarse siempre que no tenga abonos
        if order.paidAmount > 0 or (order.status != "pending" and not order.isBlocked):
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
