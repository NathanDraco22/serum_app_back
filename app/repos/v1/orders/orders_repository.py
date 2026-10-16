from core.counter_manager import CounterManager
from services.mongo_collections.v1 import DoctorsCollection, PatientsCollection
from tools.time_tools import TimeTools


from repos.v1.common.filter_params import OrderFilterParams

from .data.orders_datasource import OrdersDataSource
from .models.order_model import (
    CreateOrder,
    DoctorInfo,
    OrderInDb,
    PatientInfo,
    UpdateOrder,
)


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


        # Validar si algún ítem tiene precio modificado respecto a su precio 1 de catálogo
        has_modified_price = any(
            item.originalPrice > 0 and item.salePriceApplied != item.originalPrice
            for item in create_order.items
        )
        if has_modified_price:
            approval = order_dict.get("approval")
            if not approval or not approval.get("isApproved"):
                order_dict["isBlocked"] = True
                order_dict["approval"] = {
                    "requiresApproval": True,
                    "isApproved": False,
                    "approvedBy": None,
                    "approvedAt": None,
                    "reason": (approval.get("reason") if approval else None) or "Precio modificado arbitrariamente",
                }

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
