import pytest
from dotenv import load_dotenv

from serum.serum_config import SerumContext, serumCtx
from serum.services_initializer import init_services
from serum.repos.v1.patients import CreatePatient, PatientsRepository
from serum.repos.v1.doctors import CreateDoctor, DoctorsRepository
from serum.repos.v1.orders import CreateOrder, OrdersRepository
from serum.repos.v1.cash_shifts import CreateCashShift, CashShiftsRepository
from serum.services.mongo_collections.v1 import (
    PatientsCollection,
    DoctorsCollection,
    OrdersCollection,
    CashShiftsCollection,
    CountersCollection,
)
from app.api.v1.patients.patients_controller import patients_controller
from app.api.v1.doctors.doctors_controller import doctors_controller
from app.api.v1.orders.orders_controller import orders_controller
from app.api.v1.cash_shifts.cash_shifts_controller import cash_shifts_controller


@pytest.mark.asyncio
async def test_strict_branch_isolation():
    load_dotenv("app/.env")
    await init_services()

    # Reset test collections
    await PatientsCollection.get_instance()._collection.delete_many({})
    await DoctorsCollection.get_instance()._collection.delete_many({})
    await OrdersCollection.get_instance()._collection.delete_many({})
    await CashShiftsCollection.get_instance()._collection.delete_many({})
    await CountersCollection.get_instance()._collection.delete_many({})

    # 1. Crear Pacientes en sedes distintas
    pat_repo = PatientsRepository.get_instance()
    p_a = await pat_repo.create_patient(
        CreatePatient(
            name="Paciente Sede A",
            dateOfBirth=946684800000,
            gender="M",
            phone="1111111111",
            originBranch="BRANCH_A",
        )
    )
    p_b = await pat_repo.create_patient(
        CreatePatient(
            name="Paciente Sede B",
            dateOfBirth=946684800000,
            gender="F",
            phone="2222222222",
            originBranch="BRANCH_B",
        )
    )

    # 2. Crear Médicos en sedes distintas
    doc_repo = DoctorsRepository.get_instance()
    d_a = await doc_repo.create_doctor(
        CreateDoctor(
            name="Doctor Sede A",
            specialty="General",
            phone="3333333333",
            originBranch="BRANCH_A",
        )
    )
    d_b = await doc_repo.create_doctor(
        CreateDoctor(
            name="Doctor Sede B",
            specialty="Pediatría",
            phone="4444444444",
            originBranch="BRANCH_B",
        )
    )

    # 3. Crear Órdenes en sedes distintas
    ord_repo = OrdersRepository.get_instance()
    o_a = await ord_repo.create_order(
        CreateOrder(
            patientId=p_a.id,
            doctorId=d_a.id,
            branchId="BRANCH_A",
            items=[],
            totalPrice=10000,
        )
    )
    o_b = await ord_repo.create_order(
        CreateOrder(
            patientId=p_b.id,
            doctorId=d_b.id,
            branchId="BRANCH_B",
            items=[],
            totalPrice=15000,
        )
    )

    # 4. Crear Turnos de caja para el mismo usuario en sedes distintas
    shift_repo = CashShiftsRepository.get_instance()
    s_a = await shift_repo.open_shift(
        CreateCashShift(
            userId="cajero_1",
            branchId="BRANCH_A",
            initialBalance=5000,
            userName="Cajero Uno",
            branchName="Sucursal A",
        )
    )

    # --- VERIFICACIÓN CON CONTEXTO BRANCH_A ---
    token_a = serumCtx.set(SerumContext(branchId="BRANCH_A"))
    try:
        # Pacientes en BRANCH_A
        res_patients_a = await patients_controller.get_all_patients()
        assert len(res_patients_a.data) == 1
        assert res_patients_a.data[0].id == p_a.id
        assert res_patients_a.data[0].originBranch == "BRANCH_A"

        # Búsqueda de pacientes en BRANCH_A
        search_a = await patients_controller.search_patient_by_text("Paciente")
        assert len(search_a.data) == 1
        assert search_a.data[0].id == p_a.id

        # Médicos en BRANCH_A
        res_doctors_a = await doctors_controller.get_all_doctors()
        assert len(res_doctors_a.data) == 1
        assert res_doctors_a.data[0].id == d_a.id
        assert res_doctors_a.data[0].originBranch == "BRANCH_A"

        # Órdenes en BRANCH_A
        res_orders_a = await orders_controller.get_all_orders()
        assert len(res_orders_a.data) == 1
        assert res_orders_a.data[0].id == o_a.id
        assert res_orders_a.data[0].branchId == "BRANCH_A"

        # Turno activo en BRANCH_A
        active_shift_a = await cash_shifts_controller.get_current_shift("cajero_1")
        assert active_shift_a is not None
        assert active_shift_a.id == s_a.id
        assert active_shift_a.branchId == "BRANCH_A"
    finally:
        serumCtx.reset(token_a)

    # --- VERIFICACIÓN CON CONTEXTO BRANCH_B ---
    token_b = serumCtx.set(SerumContext(branchId="BRANCH_B"))
    try:
        # Pacientes en BRANCH_B
        res_patients_b = await patients_controller.get_all_patients()
        assert len(res_patients_b.data) == 1
        assert res_patients_b.data[0].id == p_b.id
        assert res_patients_b.data[0].originBranch == "BRANCH_B"

        # Médicos en BRANCH_B
        res_doctors_b = await doctors_controller.get_all_doctors()
        assert len(res_doctors_b.data) == 1
        assert res_doctors_b.data[0].id == d_b.id
        assert res_doctors_b.data[0].originBranch == "BRANCH_B"

        # Órdenes en BRANCH_B
        res_orders_b = await orders_controller.get_all_orders()
        assert len(res_orders_b.data) == 1
        assert res_orders_b.data[0].id == o_b.id
        assert res_orders_b.data[0].branchId == "BRANCH_B"

        # Turno activo en BRANCH_B (El usuario no tiene turno en BRANCH_B aunque tenga uno en BRANCH_A)
        active_shift_b = await cash_shifts_controller.get_current_shift("cajero_1")
        assert active_shift_b is None

        # El usuario PUEDE abrir turno en BRANCH_B sin conflicto con BRANCH_A
        s_b = await shift_repo.open_shift(
            CreateCashShift(
                userId="cajero_1",
                branchId="BRANCH_B",
                initialBalance=8000,
                userName="Cajero Uno",
                branchName="Sucursal B",
            )
        )
        assert s_b.branchId == "BRANCH_B"

        # Ahora sí tiene turno activo en BRANCH_B
        active_shift_b2 = await cash_shifts_controller.get_current_shift("cajero_1")
        assert active_shift_b2 is not None
        assert active_shift_b2.id == s_b.id
    finally:
        serumCtx.reset(token_b)
