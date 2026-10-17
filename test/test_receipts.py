import pytest
from dotenv import load_dotenv

from serum.core.counter_manager import CounterManager
from serum.core.exceptions import InvalidAmount, OrderAlreadyPaid
from serum.core.order_payment.order_payment import OrderPayIntent
from serum.core.order_payment.process_order_payment import process_order_payment
from serum.services_initializer import init_services
from serum.repos.v1.branches import BranchesRepository, CreateBranch
from serum.repos.v1.cash_shifts import CashShiftsRepository, CreateCashShift
from serum.repos.v1.common.filter_params import ReceiptFilterParams
from serum.repos.v1.common.models.user_info import UserInfo
from serum.repos.v1.orders import CreateOrder, OrdersRepository
from serum.repos.v1.orders.models.order_model import OrderItem
from serum.repos.v1.patients import CreatePatient, PatientsRepository
from serum.repos.v1.receipts import CreateReceipt, ReceiptsRepository
from serum.services.mongo_collections.v1 import (
    BranchesCollection,
    CashShiftsCollection,
    CountersCollection,
    OrdersCollection,
    PatientsCollection,
    ReceiptsCollection,
)


@pytest.mark.asyncio
async def test_receipts_system_and_flow():
    load_dotenv("app/.env")
    await init_services()

    # Reset collections
    await ReceiptsCollection.get_instance()._collection.delete_many({})
    await OrdersCollection.get_instance()._collection.delete_many({})
    await CashShiftsCollection.get_instance()._collection.delete_many({})
    await PatientsCollection.get_instance()._collection.delete_many({})
    await BranchesCollection.get_instance()._collection.delete_many({})
    await CountersCollection.get_instance()._collection.delete_many({})

    counter_mgr = CounterManager()

    # 1. Test counter
    r1 = await counter_mgr.next_receipt_number()
    r2 = await counter_mgr.next_receipt_number()
    assert r1 == "1"
    assert r2 == "2"

    await counter_mgr.set_receipt_number(50)
    r51 = await counter_mgr.next_receipt_number()
    assert r51 == "51"

    # Reset counter for entity testing
    await CountersCollection.get_instance()._collection.delete_many({})

    # 2. Test manual CRUD via ReceiptsRepository
    receipts_repo = ReceiptsRepository.get_instance()
    user_info = UserInfo(id="user-1", name="Cajero Central")

    created = await receipts_repo.create_receipt(
        CreateReceipt(
            orderId="ORD-100",
            orderNumber="100",
            branchId="BRANCH-1",
            shiftId="SHIFT-1",
            amount=25000,
            paymentMethod="cash",
            concept="Abono inicial",
            performedBy=user_info,
            patientName="Juan Pérez",
        )
    )
    assert created.id == "1"
    assert created.receiptNumber == "1"
    assert created.amount == 25000
    assert created.patientName == "Juan Pérez"
    assert created.isDeleted is False

    # List receipts
    all_receipts = await receipts_repo.get_all_receipts(
        ReceiptFilterParams(orderId="ORD-100")
    )
    assert len(all_receipts) == 1
    assert all_receipts[0].id == "1"

    # 3. Test automatic receipt generation in process_order_payment
    branch = await BranchesRepository.get_instance().create_branch(
        CreateBranch(name="Sucursal Sur", address="Av. Central 123", phone="555-0100")
    )
    patient = await PatientsRepository.get_instance().create_patient(
        CreatePatient(
            name="Maria Lopez",
            originBranch=branch.id,
            dateOfBirth=946684800000,
            gender="F",
            phone="555-1234",
        )
    )
    shift = await CashShiftsRepository.get_instance().open_shift(
        CreateCashShift(userId="user-1", branchId=branch.id, initialBalance=100000)
    )
    order = await OrdersRepository.get_instance().create_order(
        CreateOrder(
            branchId=branch.id,
            patientId=patient.id,
            items=[
                OrderItem(
                    labTestId="T1",
                    name="Hemograma",
                    salePriceApplied=30000,
                )
            ],
            totalPrice=30000,
        )
    )

    # Process partial payment (Abono)
    pay_intent = OrderPayIntent(
        orderId=order.id,
        amount=15000,
        shiftId=shift.id,
        paymentMethod="cash",
        performedBy=user_info,
    )
    updated_order = await process_order_payment(pay_intent)
    assert updated_order.paidAmount == 15000
    assert updated_order.status == "partiallyPaid"

    # Verify that a receipt was automatically created for this order
    order_receipts = await receipts_repo.get_all_receipts(
        ReceiptFilterParams(orderId=order.id)
    )
    assert len(order_receipts) == 1
    auto_receipt = order_receipts[0]
    assert auto_receipt.orderId == order.id
    assert auto_receipt.amount == 15000
    assert auto_receipt.shiftId == shift.id
    assert auto_receipt.branchId == branch.id
    assert auto_receipt.patientName == "Maria Lopez"
    assert "Abono a orden" in auto_receipt.concept

    # Process final payment (Liquidación)
    pay_intent_final = OrderPayIntent(
        orderId=order.id,
        amount=15000,
        shiftId=shift.id,
        paymentMethod="card",
        performedBy=user_info,
    )
    completed_order = await process_order_payment(pay_intent_final)
    assert completed_order.paidAmount == 30000
    assert completed_order.status in ("paid", "completed")

    # Verify second receipt was created
    order_receipts_updated = await receipts_repo.get_all_receipts(
        ReceiptFilterParams(orderId=order.id)
    )
    assert len(order_receipts_updated) == 2
    final_receipt = [r for r in order_receipts_updated if r.id != auto_receipt.id][0]
    assert final_receipt.amount == 15000
    assert final_receipt.paymentMethod == "card"
    assert "Liquidación de orden" in final_receipt.concept

    # 4. Validations
    # Non-positive amount (amount <= 0)
    with pytest.raises(InvalidAmount):
        await process_order_payment(
            OrderPayIntent(
                orderId=order.id,
                amount=0,
                shiftId=shift.id,
                paymentMethod="cash",
                performedBy=user_info,
            )
        )

    # Order is already fully paid
    with pytest.raises(OrderAlreadyPaid):
        await process_order_payment(
            OrderPayIntent(
                orderId=order.id,
                amount=5000,
                shiftId=shift.id,
                paymentMethod="cash",
                performedBy=user_info,
            )
        )

    # Overpayment on a new order with balance
    order_2 = await OrdersRepository.get_instance().create_order(
        CreateOrder(
            branchId=branch.id,
            patientId=patient.id,
            items=[
                OrderItem(
                    labTestId="T2",
                    name="Glucosa",
                    salePriceApplied=10000,
                )
            ],
            totalPrice=10000,
        )
    )
    # Trying to pay 15000 when only 10000 is owed must fail with InvalidAmount
    with pytest.raises(InvalidAmount):
        await process_order_payment(
            OrderPayIntent(
                orderId=order_2.id,
                amount=15000,
                shiftId=shift.id,
                paymentMethod="cash",
                performedBy=user_info,
            )
        )

