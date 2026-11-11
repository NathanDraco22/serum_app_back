from serum.core.counter_manager import CounterManager
from serum.repos.v1.common.models.user_info import UserInfo
from serum.services.mongo_collections.v1 import DoctorsCollection, PatientsCollection
from serum.tools.time_tools import TimeTools


from serum.repos.v1.common.filter_params import OrderFilterParams

from .data.orders_datasource import OrdersDataSource
from .models.order_model import (
    CreateOrder,
    DoctorInfo,
    OrderInDb,
    PatientInfo,
    UpdateOrder,
)
from .order_totals import calculate_order_totals, order_items_have_modified_price


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
        order_dict = create_order.model_dump()
        if create_order.patientInfo is None:
            patient_doc = await PatientsCollection.get_instance().fetch_patient_by_id(
                create_order.patientId
            )

            if patient_doc:
                order_dict["patientInfo"] = PatientInfo(
                    name=patient_doc.get("name") or "",
                    dateOfBirth=patient_doc.get("dateOfBirth") or 0,
                    gender=patient_doc.get("gender") or "M",
                    phone=patient_doc.get("phone") or "",
                    address=patient_doc.get("address") or "",
                    cardId=patient_doc.get("cardId"),
                    email=patient_doc.get("email"),
                    age=patient_doc.get("age"),
                ).model_dump()

        if create_order.doctorId and create_order.doctorInfo is None:
            doctor_doc = await DoctorsCollection.get_instance().fetch_doctor_by_id(
                create_order.doctorId
            )

            if doctor_doc:
                order_dict["doctorInfo"] = DoctorInfo(
                    name=doctor_doc.get("name") or "",
                    specialty=doctor_doc.get("specialty") or "Medicina General",
                    phone=doctor_doc.get("phone") or "",
                    cardId=doctor_doc.get("cardId"),
                    email=doctor_doc.get("email"),
                ).model_dump()


        # Validar si algún ítem tiene precio modificado respecto a su precio 1 de catálogo o si tiene descuentos
        has_modified_price = order_items_have_modified_price(create_order.items)
        has_discounts = len(create_order.discounts) > 0

        if has_modified_price or has_discounts:
            approval = order_dict.get("approval")
            if not approval or not approval.get("isApproved"):
                order_dict["isBlocked"] = True
                default_reason = (
                    "Descuento aplicado a la orden"
                    if has_discounts and not has_modified_price
                    else "Precio modificado arbitrariamente"
                )
                order_dict["approval"] = {
                    "requiresApproval": True,
                    "isApproved": False,
                    "approvedBy": None,
                    "approvedAt": None,
                    "reason": (approval.get("reason") if approval else None) or default_reason,
                }

        # Calcular totalPrice en el servidor considerando items, services y discounts.
        # El total enviado por el cliente se ignora para que sea la única fuente de verdad.
        total_price, processed_discounts = calculate_order_totals(
            order_dict.get("items", []),
            order_dict.get("services", []),
            order_dict.get("discounts", []),
        )
        order_dict["discounts"] = processed_discounts
        order_dict["totalPrice"] = total_price

        # Una orden nueva nunca nace pagada: el cobro solo se registra por el flujo de pagos.
        order_dict["paidAmount"] = 0
        order_dict["status"] = "pending"





        order_id = await CounterManager().next_order_number()
        new_order = OrderInDb(
            id=order_id,
            createdAt=TimeTools.get_now_in_milliseconds(),
            **order_dict,
        )

        result = await self.orders_ds.create_order(new_order.model_dump())
        return OrderInDb.model_validate(result)

    async def get_all_orders(
        self, filters: OrderFilterParams | None = None
    ) -> list[OrderInDb]:
        filters_dict = None
        if filters is not None:
            filters_dict = filters.model_dump(exclude_none=True)
        results = await self.orders_ds.get_all_orders(filters_dict)
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

    async def cancel_order_by_id(
        self,
        order_id: str,
        cancelled_by: UserInfo | None = None,
        reason: str | None = None,
    ) -> OrderInDb | None:
        now = TimeTools.get_now_in_milliseconds()
        cancellation_data: dict = {
            "status": "cancelled",
            "isDeleted": True,
            "updatedAt": now,
            "cancelledAt": now,
            "cancellationReason": reason,
        }
        if cancelled_by is not None:
            cancellation_data["cancelledBy"] = cancelled_by.model_dump()

        result = await self.orders_ds.cancel_order_by_id(
            order_id, cancellation_data
        )
        if result is None:
            return None
        return OrderInDb.model_validate(result)
