import pytest
from dotenv import load_dotenv

from serum.services_initializer import init_services
from serum.repos.v1.branches import BranchesRepository, CreateBranch
from serum.repos.v1.common.models.user_info import UserInfo
from serum.repos.v1.orders import (
    CreateOrder,
    OrderApproval,
    OrderDiscount,
    OrderItem,
    OrdersRepository,
)
from serum.repos.v1.patients import CreatePatient, PatientsRepository
from serum.services.mongo_collections.v1 import (
    BranchesCollection,
    CountersCollection,
    OrdersCollection,
    PatientsCollection,
)


@pytest.mark.asyncio
async def test_order_discounts_flow():
    load_dotenv("app/.env")
    await init_services()

    # Reset collections
    await OrdersCollection.get_instance()._collection.delete_many({})
    await PatientsCollection.get_instance()._collection.delete_many({})
    await BranchesCollection.get_instance()._collection.delete_many({})
    await CountersCollection.get_instance()._collection.delete_many({})

    orders_repo = OrdersRepository.get_instance()

    branch = await BranchesRepository.get_instance().create_branch(
        CreateBranch(name="Sucursal Descuentos", address="Calle Principal", phone="88888888")
    )
    patient = await PatientsRepository.get_instance().create_patient(
        CreatePatient(
            name="Paciente Descuento",
            originBranch=branch.id,
            dateOfBirth=946684800000,
            gender="M",
            phone="5550001111",
        )
    )

    # 1. Crear orden con descuento en porcentaje (ej. 10% de C$ 500 = C$ 50.00 -> 5000 centavos)
    order_1 = await orders_repo.create_order(
        CreateOrder(
            patientId=patient.id,
            branchId=branch.id,
            items=[
                OrderItem(
                    labTestId="test_1",
                    name="Hemograma Completo",
                    salePriceApplied=50000,
                    originalPrice=50000,
                )
            ],
            discounts=[
                OrderDiscount(
                    description="Descuento Tercera Edad",
                    type="percentage",
                    value=10.0,
                )
            ],
        )
    )

    assert order_1.isBlocked is True
    assert order_1.approval is not None
    assert order_1.approval.requiresApproval is True
    assert order_1.approval.isApproved is False
    assert len(order_1.discounts) == 1
    assert order_1.discounts[0].appliedAmount == 5000
    assert order_1.totalPrice == 45000

    # 2. Crear orden con descuento en monto fijo (C$ 100.00 -> 10000 centavos)
    order_2 = await orders_repo.create_order(
        CreateOrder(
            patientId=patient.id,
            branchId=branch.id,
            items=[
                OrderItem(
                    labTestId="test_2",
                    name="Perfil Lipídico",
                    salePriceApplied=40000,
                    originalPrice=40000,
                )
            ],
            discounts=[
                OrderDiscount(
                    description="Cupón Promocional",
                    type="amount",
                    value=10000.0,
                )
            ],
        )
    )

    assert order_2.isBlocked is True
    assert len(order_2.discounts) == 1
    assert order_2.discounts[0].appliedAmount == 10000
    assert order_2.totalPrice == 30000

    # 3. Crear orden con descuento pre-aprobado por supervisor
    order_3 = await orders_repo.create_order(
        CreateOrder(
            patientId=patient.id,
            branchId=branch.id,
            items=[
                OrderItem(
                    labTestId="test_3",
                    name="Glucosa",
                    salePriceApplied=20000,
                    originalPrice=20000,
                )
            ],
            discounts=[
                OrderDiscount(
                    description="Cortesía Médica",
                    type="percentage",
                    value=50.0,
                )
            ],
            approval=OrderApproval(
                requiresApproval=True,
                isApproved=True,
                approvedBy=UserInfo(id="sup_1", name="Dr. Supervisor"),
                approvedAt=1700000000000,
                reason="Autorizado por dirección",
            ),
        )
    )

    assert order_3.isBlocked is False
    assert order_3.approval is not None
    assert order_3.approval.isApproved is True
    assert order_3.discounts[0].appliedAmount == 10000
    assert order_3.totalPrice == 10000

    # 4. Retrocompatibilidad: Crear orden sin descuentos
    order_4 = await orders_repo.create_order(
        CreateOrder(
            patientId=patient.id,
            branchId=branch.id,
            items=[
                OrderItem(
                    labTestId="test_4",
                    name="Examen General de Orina",
                    salePriceApplied=15000,
                    originalPrice=15000,
                )
            ],
        )
    )

    assert order_4.isBlocked is False
    assert order_4.discounts == []
    assert order_4.totalPrice == 15000
