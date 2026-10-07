import pytest
from dotenv import load_dotenv

from core.counter_manager import CounterManager
from core.services_initializer import init_services
from repos.v1.cash_shifts import CashShiftsRepository, CreateCashShift
from repos.v1.doctors import CreateDoctor, DoctorsRepository
from repos.v1.orders import CreateOrder, OrdersRepository
from repos.v1.patients import CreatePatient, PatientsRepository
from repos.v1.quotations import CreateQuotation, QuotationsRepository
from services.mongo_collections.v1 import (
    CashShiftsCollection,
    CountersCollection,
    DoctorsCollection,
    OrdersCollection,
    PatientsCollection,
    QuotationsCollection,
)



@pytest.mark.asyncio
async def test_counter_manager_and_entity_ids():
    load_dotenv("app/.env")
    await init_services()


    # Reset counters collection for this test
    counters_col = CountersCollection.get_instance()._collection
    await counters_col.delete_many({})

    counter_mgr = CounterManager()

    # 1. Patients: formatted to 4 digits (zfill 4)
    p1 = await counter_mgr.next_patient_number()
    p2 = await counter_mgr.next_patient_number()
    assert p1 == "0001"
    assert p2 == "0002"

    # 2. Doctors: formatted to 4 digits (zfill 4)
    d1 = await counter_mgr.next_doctor_number()
    d2 = await counter_mgr.next_doctor_number()
    assert d1 == "0001"
    assert d2 == "0002"

    # 3. Orders: numeric string without leading zeros
    o1 = await counter_mgr.next_order_number()
    o2 = await counter_mgr.next_order_number()
    assert o1 == "1"
    assert o2 == "2"

    # 4. Quotations: numeric string without leading zeros
    q1 = await counter_mgr.next_quotation_number()
    q2 = await counter_mgr.next_quotation_number()
    assert q1 == "1"
    assert q2 == "2"

    # 5. Shifts: numeric string without leading zeros
    s1 = await counter_mgr.next_shift_number()
    s2 = await counter_mgr.next_shift_number()
    assert s1 == "1"
    assert s2 == "2"

    # 6. Setters
    await counter_mgr.set_patient_number(99)
    p100 = await counter_mgr.next_patient_number()
    assert p100 == "0100"

    await counter_mgr.set_order_number(499)
    o500 = await counter_mgr.next_order_number()
    assert o500 == "500"

    await counter_mgr.set_shift_number(9)
    s10 = await counter_mgr.next_shift_number()
    assert s10 == "10"

    # --- Creación de Entidades usando Repositorios ---

    # Reset collections
    await PatientsCollection.get_instance()._collection.delete_many({})
    await DoctorsCollection.get_instance()._collection.delete_many({})
    await OrdersCollection.get_instance()._collection.delete_many({})
    await QuotationsCollection.get_instance()._collection.delete_many({})
    await CashShiftsCollection.get_instance()._collection.delete_many({})
    await counters_col.delete_many({})


    # 1. Crear Paciente
    patients_repo = PatientsRepository.get_instance()
    patient1 = await patients_repo.create_patient(
        CreatePatient(
            name="Juan Perez",
            dateOfBirth=946684800000,
            gender="M",
            phone="1234567890",
            originBranch="ORIGIN_BRANCH",
        )
    )
    assert patient1.id == "0001"

    patient2 = await patients_repo.create_patient(
        CreatePatient(
            name="Maria Gomez",
            dateOfBirth=946684800000,
            gender="F",
            phone="9876543210",
            originBranch="ORIGIN_BRANCH",
        )
    )
    assert patient2.id == "0002"

    # 2. Crear Doctor
    doctors_repo = DoctorsRepository.get_instance()
    doctor1 = await doctors_repo.create_doctor(
        CreateDoctor(
            name="Dr. Carlos Slim",
            specialty="Cardiologia",
            originBranch="ORIGIN_BRANCH",
        )
    )
    assert doctor1.id == "0001"

    # 3. Crear Orden
    orders_repo = OrdersRepository.get_instance()
    order1 = await orders_repo.create_order(
        CreateOrder(
            branchId="ORIGIN_BRANCH",
            patientId=patient1.id,
            doctorId=doctor1.id,
        )
    )
    assert order1.id == "1"
    assert order1.patientId == "0001"
    assert order1.doctorId == "0001"

    order2 = await orders_repo.create_order(
        CreateOrder(
            branchId="ORIGIN_BRANCH",
            patientId=patient2.id,
        )
    )
    assert order2.id == "2"

    # 4. Crear Cotización
    quotations_repo = QuotationsRepository.get_instance()
    quotation1 = await quotations_repo.create_quotation(
        CreateQuotation(
            branchId="ORIGIN_BRANCH",
            clientName="Empresa Salud SA",
        )
    )
    assert quotation1.id == "1"

    quotation2 = await quotations_repo.create_quotation(
        CreateQuotation(
            branchId="ORIGIN_BRANCH",
            clientName="Clinica Dental",
        )
    )
    assert quotation2.id == "2"

    # 5. Abrir Turnos de Caja
    shifts_repo = CashShiftsRepository.get_instance()
    shift1 = await shifts_repo.open_shift(
        CreateCashShift(
            userId="user_1",
            branchId="ORIGIN_BRANCH",
            initialBalance=1000,
        )
    )
    assert shift1.id == "1"

    shift2 = await shifts_repo.open_shift(
        CreateCashShift(
            userId="user_2",
            branchId="ORIGIN_BRANCH",
            initialBalance=2000,
        )
    )
    assert shift2.id == "2"

