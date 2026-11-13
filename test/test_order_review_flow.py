from types import SimpleNamespace

import pytest
from dotenv import load_dotenv
from fastapi import HTTPException, Request

from serum.services_initializer import init_services
from serum.repos.v1.branches import BranchesRepository, CreateBranch
from serum.repos.v1.orders import (
    CreateOrder,
    OrderItem,
    UpdateOrder,
)
from serum.repos.v1.orders.models.order_model import OrderTestResult
from serum.repos.v1.patients import CreatePatient, PatientsRepository
from serum.services.mongo_collections.v1 import (
    BranchesCollection,
    CountersCollection,
    OrdersCollection,
    PatientsCollection,
)
from api.v1.orders.orders_controller import orders_controller
from api.v1.orders.orders_presenter import with_legacy_status
from api.v1.orders.orders_schemas import OrderReopenRequest


def _request_with_user(user_id: str, name: str, access_level: int) -> Request:
    req = Request(scope={"type": "http", "headers": []})
    req.state.user = SimpleNamespace(id=user_id, name=name, accessLevel=access_level)
    return req


@pytest.mark.asyncio
async def test_order_review_finalize_and_reopen_flow():
    load_dotenv("app/.env")
    await init_services()

    await OrdersCollection.get_instance()._collection.delete_many({})
    await PatientsCollection.get_instance()._collection.delete_many({})
    await BranchesCollection.get_instance()._collection.delete_many({})
    await CountersCollection.get_instance()._collection.delete_many({})

    branch = await BranchesRepository.get_instance().create_branch(
        CreateBranch(name="Sucursal Revisión", address="Calle 2", phone="22223333")
    )
    patient = await PatientsRepository.get_instance().create_patient(
        CreatePatient(
            name="Paciente Revisión",
            originBranch=branch.id,
            dateOfBirth=946684800000,
            gender="F",
            phone="5550000000",
        )
    )

    operator_req = _request_with_user("user-3", "Bioanalista", 3)
    readonly_req = _request_with_user("user-1", "Consulta", 1)

    order = await orders_controller.create_order(
        CreateOrder(
            branchId=branch.id,
            patientId=patient.id,
            items=[
                OrderItem(
                    labTestId="test-review-1",
                    name="Glucosa",
                    salePriceApplied=10000,
                    originalPrice=10000,
                )
            ],
            totalPrice=10000,
            results=[
                OrderTestResult(
                    labTestId="test-review-1",
                    parameterName="Glucosa",
                    dataType="numeric",
                )
            ],
        ),
        operator_req,
    )

    assert order.status == "pending"
    assert order.statusHistory[-1].status == "pending"

    # Capturar todos los resultados deja la orden en revisión, sin importar el pago.
    in_review = await orders_controller.update_order_by_id(
        order.id,
        UpdateOrder(
            results=[
                OrderTestResult(
                    labTestId="test-review-1",
                    parameterName="Glucosa",
                    dataType="numeric",
                    resultValue="95",
                )
            ]
        ),
        operator_req,
    )

    assert in_review.status == "in_review"
    assert in_review.paidAmount == 0
    assert in_review.statusHistory[-1].status == "in_review"
    assert with_legacy_status(in_review).status == "in_review"

    # Nivel 1 no puede finalizar ni reabrir.
    with pytest.raises(HTTPException) as finalize_forbidden:
        await orders_controller.finalize_order(order.id, readonly_req)
    assert finalize_forbidden.value.status_code == 403

    # Finalización explícita (la orden sigue sin pagar).
    finalized = await orders_controller.finalize_order(order.id, operator_req)
    assert finalized.status == "completed"
    assert finalized.finalizedAt is not None
    assert finalized.finalizedBy is not None
    assert finalized.finalizedBy.name == "Bioanalista"
    assert finalized.statusHistory[-1].status == "completed"

    with pytest.raises(HTTPException) as reopen_forbidden:
        await orders_controller.reopen_order(
            order.id,
            OrderReopenRequest(reason="Intento sin permisos"),
            readonly_req,
        )
    assert reopen_forbidden.value.status_code == 403

    # Reapertura con motivo y auditoría.
    reopened = await orders_controller.reopen_order(
        order.id,
        OrderReopenRequest(reason="Corrección de glucosa"),
        operator_req,
    )
    assert reopened.status == "in_review"
    assert reopened.finalizedAt is None
    assert reopened.finalizedBy is None
    assert reopened.reopenedAt is not None
    assert reopened.reopenedBy is not None
    assert reopened.reopenedBy.name == "Bioanalista"
    assert reopened.reopenReason == "Corrección de glucosa"
    assert reopened.revisionCount == 1
    assert reopened.statusHistory[-1].status == "in_review"
    assert with_legacy_status(reopened).status == "in_review"

    # El historial conserva la finalización anterior.
    statuses = [entry.status for entry in reopened.statusHistory]
    assert statuses == ["pending", "in_review", "completed", "in_review"]
