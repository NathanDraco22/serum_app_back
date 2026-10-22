import pytest
from dotenv import load_dotenv
from fastapi import Request

from serum.core.exceptions import OrderIsBlocked
from serum.core.order_payment.order_payment import OrderPayIntent
from serum.core.order_payment.order_payment_manager import OrderPaymentManager
from serum.services_initializer import init_services
from serum.repos.v1.branches import BranchesRepository, CreateBranch
from serum.repos.v1.cash_registers import CashRegistersRepository, CreateCashRegister
from serum.repos.v1.cash_shifts import CashShiftsRepository, CreateCashShift
from serum.repos.v1.common.models.user_info import UserInfo
from serum.repos.v1.orders import (
    CreateOrder,
    OrderItem,
    OrdersRepository,
    UpdateOrder,
)
from serum.repos.v1.orders.models.order_model import OrderTestResult
from serum.repos.v1.patients import CreatePatient, PatientsRepository
from serum.repos.v1.users import CreateUser, UsersRepository
from serum.services.mongo_collections.v1 import (
    BranchesCollection,
    CashRegistersCollection,
    CashShiftsCollection,
    CountersCollection,
    OrdersCollection,
    PatientsCollection,
    UsersCollection,
)
from api.v1.orders.orders_controller import orders_controller
from api.v1.orders.orders_schemas import OrderApproveRequest


@pytest.mark.asyncio
async def test_order_blocking_and_approval_flow():
    load_dotenv("app/.env")
    await init_services()

    # Reset collections
    await OrdersCollection.get_instance()._collection.delete_many({})
    await CashShiftsCollection.get_instance()._collection.delete_many({})
    await CashRegistersCollection.get_instance()._collection.delete_many({})
    await PatientsCollection.get_instance()._collection.delete_many({})
    await BranchesCollection.get_instance()._collection.delete_many({})
    await UsersCollection.get_instance()._collection.delete_many({})
    await CountersCollection.get_instance()._collection.delete_many({})

    # 1. Setup Branch, Patient, Register, Shift and Users
    branch = await BranchesRepository.get_instance().create_branch(
        CreateBranch(name="Sucursal Bloqueo", address="Calle 1", phone="12345678")
    )
    patient = await PatientsRepository.get_instance().create_patient(
        CreatePatient(
            name="Paciente Prueba",
            originBranch=branch.id,
            dateOfBirth=946684800000,
            gender="M",
            phone="5551234567",
        )
    )
    register = await CashRegistersRepository.get_instance().create_cash_register(
        CreateCashRegister(name="Caja 1", branchId=branch.id)
    )

    # Supervisor user (accessLevel 4)
    _ = await UsersRepository.get_instance().create_user(
        CreateUser(
            username="supervisor1",
            password="SuperSecret123",
            name="Dra. Supervisora",
            role="Supervisor",
            accessLevel=4,
            branches=[branch.id],
        )
    )

    # Operator user (accessLevel 3)
    operator = await UsersRepository.get_instance().create_user(
        CreateUser(
            username="operador1",
            password="OperadorSecret",
            name="Operador Ventanilla",
            role="Operador",
            accessLevel=3,
            branches=[branch.id],
        )
    )

    shift = await CashShiftsRepository.get_instance().open_shift(
        CreateCashShift(
            branchId=branch.id,
            userId=operator.id,
            userName=operator.name,
            initialBalance=10000,
        )
    )

    # 2. Crear orden con precio modificado (originalPrice=10000, salePriceApplied=7500)
    orders_repo = OrdersRepository.get_instance()
    order_create = CreateOrder(
        branchId=branch.id,
        patientId=patient.id,
        items=[
            OrderItem(
                labTestId="test-1",
                name="Glucosa Especial",
                salePriceApplied=7500,
                originalPrice=10000,
            )
        ],
        totalPrice=7500,
        results=[
            OrderTestResult(
                labTestId="test-1",
                parameterName="Glucosa",
                dataType="numeric",
            )
        ],
    )

    order = await orders_repo.create_order(order_create)
    assert order.isBlocked is True
    assert order.approval is not None
    assert order.approval.requiresApproval is True
    assert order.approval.isApproved is False

    # 3. Intentar cobrar una orden bloqueada debe fallar con OrderIsBlocked
    payment_mgr = OrderPaymentManager()
    pay_intent = OrderPayIntent(
        orderId=order.id,
        amount=7500,
        shiftId=shift.id,
        registerId=register.id,
        paymentMethod="cash",
        performedBy=UserInfo(id=operator.id, name=operator.name),
    )

    with pytest.raises(OrderIsBlocked):
        await payment_mgr.pay_order(pay_intent)

    # 4. Intentar actualizar resultados clínicos en una orden bloqueada debe fallar
    with pytest.raises(OrderIsBlocked):
        await orders_controller.update_order_by_id(
            order.id,
            UpdateOrder(
                results=[
                    OrderTestResult(
                        labTestId="test-1",
                        parameterName="Glucosa",
                        dataType="numeric",
                        resultValue="95",
                    )
                ]
            ),
        )

    # 5. Desbloqueo mediante credenciales de Supervisor en ventanilla (POST /approve)
    req_mock = Request(scope={"type": "http", "headers": []})
    approve_req = OrderApproveRequest(
        supervisorUsername="supervisor1",
        supervisorPassword="SuperSecret123",
        reason="Descuento autorizado por cortesía médica",
    )

    approved_order = await orders_controller.approve_order(
        order_id=order.id,
        body=approve_req,
        req=req_mock,
    )

    assert approved_order.isBlocked is False
    assert approved_order.approval is not None
    assert approved_order.approval.isApproved is True
    assert approved_order.approval.approvedBy is not None
    assert approved_order.approval.approvedBy.name == "Dra. Supervisora"

    # 6. Cobrar la orden ahora desbloqueada debe tener éxito
    paid_order = await payment_mgr.pay_order(pay_intent)
    assert paid_order.paidAmount == 7500
    assert paid_order.status == "paid"

    # 7. Capturar resultados en la orden ya desbloqueada y pagada debe funcionar
    updated_with_results = await orders_controller.update_order_by_id(
        order.id,
        UpdateOrder(
            results=[
                OrderTestResult(
                    labTestId="test-1",
                    parameterName="Glucosa",
                    dataType="numeric",
                    resultValue="95",
                )
            ]
        ),
    )
    assert updated_with_results.results[0].resultValue == "95"

    # 8. Verificar que una orden bloqueada con $0 pagados PUEDE eliminarse
    blocked_order_2 = await orders_repo.create_order(
        CreateOrder(
            branchId=branch.id,
            patientId=patient.id,
            items=[
                OrderItem(
                    labTestId="test-2",
                    name="Hemograma Especial",
                    salePriceApplied=5000,
                    originalPrice=8000,
                )
            ],
            totalPrice=5000,
        )
    )
    assert blocked_order_2.isBlocked is True

    deleted = await orders_controller.delete_order_by_id(blocked_order_2.id)
    assert deleted.id == blocked_order_2.id

    verify_deleted = await orders_repo.get_order_by_id(blocked_order_2.id)
    assert verify_deleted is None

    # 9. Consultar órdenes del paciente a través del nuevo endpoint/método
    patient_orders = await orders_controller.get_orders_by_patient_id(patient.id)
    assert patient_orders.count >= 1
    assert any(o.id == order.id for o in patient_orders.data)
