from fastapi import HTTPException, Request, status
from serum.serum_config import serumCtx

from serum.core.exceptions import (
    OrderCannotBeDeleted,
    OrderHasClinicalResults,
    OrderHasPayments,
    OrderIsBlocked,
)
from serum.core.order_payment.order_payment import OrderPayIntent
from serum.core.order_payment.order_payment_manager import OrderPaymentManager
from serum.core.security import SysPasswordHasher, TokenManager
from serum.repos.v1.common.filter_params import (
    OrderFilterParams,
    ReceiptFilterParams,
)
from serum.repos.v1.common.models.user_info import UserInfo
from serum.repos.v1.orders import (
    CreateOrder,
    OrderApproval,
    OrderInDb,
    OrderStatusChange,
    OrdersRepository,
    UpdateOrder,
)
from serum.repos.v1.orders.order_totals import (
    calculate_order_totals,
    order_items_have_modified_price,
)
from serum.repos.v1.receipts import ReceiptsRepository
from serum.repos.v1.users import UsersRepository
from responses.v1 import ListResponse
from serum.tools.time_tools import TimeTools

from .orders_presenter import with_legacy_status
from .orders_schemas import OrderApproveRequest, OrderPayRequest, OrderReopenRequest


class OrdersController:
    def __init__(self, orders_repo: OrdersRepository) -> None:
        self.orders_repo = orders_repo
        self.order_payment_manager = OrderPaymentManager()
        self.users_repo = UsersRepository.get_instance()
        self.receipts_repo = ReceiptsRepository.get_instance()

    @staticmethod
    def _resolve_actor(req: Request | None) -> tuple[UserInfo | None, int]:
        if req is None:
            return None, 0

        user = getattr(req.state, "user", None)
        if user is not None:
            return UserInfo(id=user.id, name=user.name), user.accessLevel

        api_key = getattr(req.state, "api_key", None)
        if api_key is not None:
            return UserInfo(id=api_key.id, name=api_key.name), 0

        return None, 0

    @staticmethod
    def _require_clinical_access(access_level: int) -> None:
        if access_level < 3:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Se requiere nivel de acceso 3 o superior para finalizar "
                    "o reabrir una orden clínica"
                ),
            )

    @staticmethod
    def _append_status_history(
        order: OrderInDb,
        status: str,
        actor: UserInfo | None,
        changed_at: int,
        reason: str | None = None,
    ) -> list[dict]:
        history = [entry.model_dump() for entry in order.statusHistory]
        history.append(
            OrderStatusChange(
                status=status,
                changedAt=changed_at,
                changedBy=actor,
                reason=reason,
            ).model_dump()
        )
        return history

    @staticmethod
    def _results_are_complete(results: list) -> bool:
        return bool(results) and all(
            result.resultValue is not None
            and str(result.resultValue).strip() != ""
            for result in results
        )

    def _finalize_payload(
        self,
        order: OrderInDb,
        actor: UserInfo | None,
        now: int,
        results: list | None = None,
    ) -> dict:
        if order.isBlocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "La orden está bloqueada por modificación de precio. "
                    "Requiere autorización antes de finalizarse."
                ),
            )
        effective_results = results if results is not None else order.results
        if not self._results_are_complete(effective_results):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Todos los resultados deben estar capturados para finalizar la orden",
            )

        return {
            "status": "completed",
            "finalizedAt": now,
            "finalizedBy": actor,
            "statusHistory": self._append_status_history(
                order, "completed", actor, now, "Orden finalizada"
            ),
        }

    def _reopen_payload(
        self,
        order: OrderInDb,
        actor: UserInfo | None,
        now: int,
        reason: str,
    ) -> dict:
        return {
            "status": "in_review",
            "finalizedAt": None,
            "finalizedBy": None,
            "reopenedAt": now,
            "reopenedBy": actor,
            "reopenReason": reason,
            "revisionCount": order.revisionCount + 1,
            "statusHistory": self._append_status_history(
                order, "in_review", actor, now, reason
            ),
        }

    async def create_order(
        self, body: CreateOrder, req: Request | None = None
    ) -> OrderInDb:
        actor, _ = self._resolve_actor(req)
        order = await self.orders_repo.create_order(body, actor=actor)
        return with_legacy_status(order)

    async def get_all_orders(
        self, query_params: OrderFilterParams | None = None
    ) -> ListResponse[OrderInDb]:
        if query_params is None:
            query_params = OrderFilterParams()
        if query_params.branchId is None and serumCtx.get().branchId:
            query_params.branchId = serumCtx.get().branchId

        orders = await self.orders_repo.get_all_orders(query_params)
        orders = [with_legacy_status(order) for order in orders]
        return ListResponse(count=len(orders), data=orders)

    async def get_orders_by_patient_id(
        self,
        patient_id: str,
        branch_id: str | None = None,
        all_branches: bool = True,
    ) -> ListResponse[OrderInDb]:
        query_params = OrderFilterParams(patientId=patient_id)
        if not all_branches:
            if branch_id:
                query_params.branchId = branch_id
            elif serumCtx.get().branchId:
                query_params.branchId = serumCtx.get().branchId

        orders = await self.orders_repo.get_all_orders(query_params)
        orders = [with_legacy_status(order) for order in orders]
        return ListResponse(count=len(orders), data=orders)

    async def get_order_by_id(self, order_id: str) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return with_legacy_status(order)

    async def pay_order(self, order_id: str, body: OrderPayRequest) -> OrderInDb:
        pay_intent = OrderPayIntent(
            orderId=order_id,
            amount=body.amount,
            shiftId=body.shiftId,
            registerId=body.registerId,
            paymentMethod=body.paymentMethod,
            performedBy=body.performedBy,
            referenceNumber=body.referenceNumber,
            bank=body.bank,
        )
        order = await self.order_payment_manager.pay_order(pay_intent)
        return with_legacy_status(order)

    async def update_order_by_id(
        self,
        order_id: str,
        body: UpdateOrder,
        req: Request | None = None,
    ) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        if order.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede modificar una orden cancelada",
            )

        # No permitir capturar ni alterar resultados si la orden se encuentra bloqueada
        if order.isBlocked and body.results is not None:
            raise OrderIsBlocked()

        financial_change = (
            body.items is not None
            or body.services is not None
            or body.discounts is not None
        )

        if financial_change and order.paidAmount > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden modificar los valores financieros de una orden con pagos registrados",
            )
        if financial_change and order.status in ("completed", "in_review"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No se pueden modificar los exámenes de una orden "
                    "completada o en revisión"
                ),
            )

        # El cliente puede seguir enviando campos financieros por compatibilidad,
        # pero el servidor los descarta y los recalcula.
        sanitized = body.model_dump(exclude_unset=True, exclude_none=True)
        sanitized.pop("paidAmount", None)
        sanitized.pop("totalPrice", None)
        sanitized.pop("branchId", None)
        sanitized.pop("isBlocked", None)
        sanitized.pop("approval", None)
        # La auditoría clínica se reconstruye en el servidor; nunca se acepta
        # desde el cuerpo del cliente.
        sanitized.pop("statusHistory", None)
        sanitized.pop("finalizedAt", None)
        sanitized.pop("finalizedBy", None)
        sanitized.pop("reopenedAt", None)
        sanitized.pop("reopenedBy", None)
        sanitized.pop("reopenReason", None)
        sanitized.pop("revisionCount", None)
        incoming_status = sanitized.pop("status", None)

        actor, access_level = self._resolve_actor(req)

        effective_items = body.items if body.items is not None else order.items
        effective_services = (
            body.services if body.services is not None else order.services
        )
        effective_discounts = (
            body.discounts if body.discounts is not None else order.discounts
        )

        effective_total = order.totalPrice

        if financial_change:
            effective_total, processed_discounts = calculate_order_totals(
                effective_items,
                effective_services,
                effective_discounts,
            )
            sanitized["totalPrice"] = effective_total
            sanitized["discounts"] = processed_discounts

            has_modified_price = order_items_have_modified_price(effective_items)
            has_discounts = len(processed_discounts) > 0

            if has_modified_price or has_discounts:
                already_approved = (
                    order.approval is not None and order.approval.isApproved
                )
                if already_approved:
                    pass
                elif actor is not None and access_level > 3:
                    sanitized["isBlocked"] = False
                    sanitized["approval"] = OrderApproval(
                        requiresApproval=True,
                        isApproved=True,
                        approvedBy=actor,
                        approvedAt=TimeTools.get_now_in_milliseconds(),
                        reason="Autorizado por supervisor en edición de orden",
                    ).model_dump()
                else:
                    sanitized["isBlocked"] = True
                    sanitized["approval"] = OrderApproval(
                        requiresApproval=True,
                        isApproved=False,
                        approvedBy=None,
                        approvedAt=None,
                        reason="Precio modificado o descuento aplicado en la edición",
                    ).model_dump()

        # Normalizar el estado clínico. Los estados financieros legacy del body
        # (paid/partiallyPaid) se siguen aceptando por compatibilidad, pero el
        # estado financiero real se calcula a partir de paidAmount al responder.
        now = TimeTools.get_now_in_milliseconds()
        effective_results = (
            body.results if body.results is not None else order.results
        )
        all_results_complete = self._results_are_complete(effective_results)

        if incoming_status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use el endpoint de cancelación de órdenes",
            )
        if incoming_status == "in_review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use el endpoint de reapertura de órdenes",
            )

        target_status = order.status
        history_reason: str | None = None

        if incoming_status == "completed":
            self._require_clinical_access(access_level)
            if order.status != "completed":
                sanitized.update(
                    self._finalize_payload(
                        order,
                        actor,
                        now,
                        results=effective_results,
                    )
                )
                target_status = "completed"
        elif incoming_status in ("pending", "paid", "partiallyPaid"):
            if order.status == "completed":
                self._require_clinical_access(access_level)
                if not order.results:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="La orden no tiene resultados clínicos para reabrir",
                    )
                sanitized.update(
                    self._reopen_payload(
                        order,
                        actor,
                        now,
                        "Reapertura desde cliente anterior",
                    )
                )
                target_status = "in_review"
            elif order.status == "pending":
                target_status = "pending"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Use la actualización de resultados para cambiar una "
                        "orden en revisión"
                    ),
                )
        elif body.results is not None:
            if order.status == "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reabra la orden antes de modificar sus resultados",
                )
            if all_results_complete:
                target_status = "in_review"
                if order.status != "in_review":
                    history_reason = "Resultados completados"
            else:
                target_status = "pending"
                if order.status == "in_review":
                    history_reason = "Resultados incompletos"

        if target_status != order.status:
            sanitized["status"] = target_status
            # Las finalizaciones y reaperturas ya insertaron su propio historial.
            if "statusHistory" not in sanitized:
                sanitized["statusHistory"] = self._append_status_history(
                    order, target_status, actor, now, history_reason
                )

        update_model = UpdateOrder(**sanitized)
        updated_order = await self.orders_repo.update_order_by_id(
            order_id, update_model
        )
        if updated_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return with_legacy_status(updated_order)

    async def finalize_order(self, order_id: str, req: Request) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        actor, access_level = self._resolve_actor(req)
        self._require_clinical_access(access_level)

        if order.status != "in_review":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden no está en revisión",
            )

        now = TimeTools.get_now_in_milliseconds()
        update_model = UpdateOrder(
            **self._finalize_payload(order, actor, now)
        )
        updated = await self.orders_repo.update_order_by_id(
            order_id, update_model
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return with_legacy_status(updated)

    async def reopen_order(
        self,
        order_id: str,
        body: OrderReopenRequest,
        req: Request,
    ) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        actor, access_level = self._resolve_actor(req)
        self._require_clinical_access(access_level)

        if order.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden reabrir órdenes finalizadas",
            )

        if not order.results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La orden no tiene resultados clínicos para reabrir",
            )

        reason = body.reason.strip()
        if not reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El motivo de reapertura es obligatorio",
            )

        now = TimeTools.get_now_in_milliseconds()
        update_model = UpdateOrder(
            **self._reopen_payload(order, actor, now, reason)
        )
        updated = await self.orders_repo.update_order_by_id(
            order_id, update_model
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return with_legacy_status(updated)

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
        return with_legacy_status(updated)

    async def delete_order_by_id(
        self,
        order_id: str,
        req: Request | None = None,
        reason: str | None = None,
    ) -> OrderInDb:
        order = await self.orders_repo.get_order_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        receipts = await self.receipts_repo.get_all_receipts(
            ReceiptFilterParams(orderId=order_id)
        )
        if order.paidAmount > 0 or receipts:
            raise OrderHasPayments()

        has_clinical_results = order.status == "completed" or any(
            (result.resultValue or "").strip() for result in order.results
        )
        if has_clinical_results:
            raise OrderHasClinicalResults()

        # Una orden bloqueada o pendiente puede cancelarse si no tiene cobros
        # ni resultados clínicos.
        if order.status != "pending" and not order.isBlocked:
            raise OrderCannotBeDeleted()

        actor, _ = self._resolve_actor(req)
        cancellation_data = {
            "statusHistory": self._append_status_history(
                order,
                "cancelled",
                actor,
                TimeTools.get_now_in_milliseconds(),
                reason or "Cancelación de orden",
            )
        }
        cancelled_order = await self.orders_repo.cancel_order_by_id(
            order_id,
            cancelled_by=actor,
            reason=reason,
            extra_data=cancellation_data,
        )
        if cancelled_order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        return with_legacy_status(cancelled_order)


orders_controller = OrdersController(
    orders_repo=OrdersRepository.get_instance(),
)
