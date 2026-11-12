from typing import Any

import pytest
from pydantic import ValidationError

from serum.core.exceptions import (
    InvalidPatientDemographics,
    OrderHasClinicalResults,
)
from serum.repos.v1.orders import (
    CreateOrder,
    OrdersDataSource,
    OrdersRepository,
    UpdateOrder,
)
from serum.repos.v1.orders.models.order_model import (
    OrderInDb,
    OrderTestResult,
    PatientInfo,
)
from serum.repos.v1.orders.orders_repository import (
    _has_captured_results,
    _has_valid_patient_demographics,
)
from serum.repos.v1.patients import CreatePatient, UpdatePatient
from serum.services.mongo_collections.v1 import PatientsCollection
from serum.tools.time_tools import TimeTools


class _FakeOrdersDataSource(OrdersDataSource):
    def __init__(self, existing: OrderInDb) -> None:
        self.existing = existing
        self.last_update: dict | None = None

    async def get_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        return self.existing.model_dump()

    async def update_order_by_id(
        self, order_id: str, order: dict[str, Any]
    ) -> dict[str, Any] | None:
        self.last_update = order
        merged = self.existing.model_dump()
        merged.update(order)
        return merged


def _order(
    *,
    patient_info: PatientInfo | None = None,
    results: list[OrderTestResult] | None = None,
) -> OrderInDb:
    return OrderInDb(
        id="ord-1",
        branchId="branch-1",
        patientId="pat-1",
        patientInfo=patient_info,
        results=results or [],
        createdAt=1,
    )


def test_create_patient_requires_age_or_date_of_birth() -> None:
    with pytest.raises(ValidationError):
        CreatePatient(
            name="Sin datos",
            dateOfBirth=0,
            gender="M",
            phone="1",
            originBranch="branch-1",
        )

    patient = CreatePatient(
        name="Solo edad",
        dateOfBirth=0,
        age=30,
        gender="M",
        phone="1",
        originBranch="branch-1",
    )
    assert patient.age == 30


def test_create_patient_rejects_future_date_of_birth() -> None:
    future = TimeTools.get_now_in_milliseconds() + 86_400_000

    with pytest.raises(ValidationError):
        CreatePatient(
            name="Futuro",
            dateOfBirth=future,
            gender="M",
            phone="1",
            originBranch="branch-1",
        )


def test_update_patient_cannot_clear_date_of_birth() -> None:
    with pytest.raises(ValidationError):
        UpdatePatient(dateOfBirth=None)


def test_update_patient_accepts_age_only_update() -> None:
    update = UpdatePatient(age=30)

    assert update.age == 30
    assert update.model_fields_set == {"age"}


def test_has_valid_patient_demographics() -> None:
    assert _has_valid_patient_demographics(None) is False
    assert _has_valid_patient_demographics(PatientInfo(name="Sin datos")) is False
    assert _has_valid_patient_demographics(PatientInfo(name="RN", age=0)) is True
    assert (
        _has_valid_patient_demographics(PatientInfo(name="Con fecha", dateOfBirth=123))
        is True
    )
    assert _has_valid_patient_demographics({"dateOfBirth": 123}) is True
    assert _has_valid_patient_demographics({"dateOfBirth": 0, "age": 30}) is True


def test_has_captured_results() -> None:
    with_value = _order(
        results=[
            OrderTestResult(
                labTestId="t-1",
                parameterName="Glucosa",
                dataType="numeric",
                resultValue="100",
            )
        ]
    )
    empty_value = _order(
        results=[
            OrderTestResult(
                labTestId="t-1",
                parameterName="Glucosa",
                dataType="numeric",
            )
        ]
    )

    assert _has_captured_results(with_value) is True
    assert _has_captured_results(empty_value) is False


@pytest.mark.asyncio
async def test_create_order_rejects_invalid_client_snapshot() -> None:
    ds = _FakeOrdersDataSource(_order())
    repo = OrdersRepository(ds)

    with pytest.raises(InvalidPatientDemographics):
        await repo.create_order(
            CreateOrder(
                branchId="branch-1",
                patientId="pat-1",
                patientInfo=PatientInfo(name="Sin datos"),
            )
        )


@pytest.mark.asyncio
async def test_create_order_rejects_patient_without_demographics(monkeypatch) -> None:
    ds = _FakeOrdersDataSource(_order())
    repo = OrdersRepository(ds)

    async def fake_fetch_patient(patient_id: str):
        return {
            "name": "Sin datos",
            "dateOfBirth": 0,
            "gender": "M",
            "phone": "5",
            "address": "",
            "age": None,
        }

    patients = PatientsCollection.get_instance()
    monkeypatch.setattr(patients, "fetch_patient_by_id", fake_fetch_patient)

    with pytest.raises(InvalidPatientDemographics):
        await repo.create_order(CreateOrder(branchId="branch-1", patientId="pat-1"))


@pytest.mark.asyncio
async def test_update_order_preserves_snapshot_when_patient_does_not_change() -> None:
    existing = _order(
        patient_info=PatientInfo(
            name="Original",
            dateOfBirth=946684800000,
            gender="M",
        )
    )
    ds = _FakeOrdersDataSource(existing)
    repo = OrdersRepository(ds)

    updated = await repo.update_order_by_id(
        "ord-1",
        UpdateOrder(
            patientId="pat-1",
            patientInfo=PatientInfo(name="Alterado", dateOfBirth=0),
        ),
    )

    assert ds.last_update is not None
    assert "patientInfo" not in ds.last_update
    assert updated is not None
    assert updated.patientInfo is not None
    assert updated.patientInfo.name == "Original"


@pytest.mark.asyncio
async def test_update_order_blocks_patient_change_with_captured_results() -> None:
    existing = _order(
        patient_info=PatientInfo(
            name="Original",
            dateOfBirth=946684800000,
            gender="M",
        ),
        results=[
            OrderTestResult(
                labTestId="t-1",
                parameterName="Glucosa",
                dataType="numeric",
                resultValue="100",
            )
        ],
    )
    ds = _FakeOrdersDataSource(existing)
    repo = OrdersRepository(ds)

    with pytest.raises(OrderHasClinicalResults):
        await repo.update_order_by_id("ord-1", UpdateOrder(patientId="pat-2"))


@pytest.mark.asyncio
async def test_update_order_rebuilds_snapshot_for_new_patient(monkeypatch) -> None:
    existing = _order(
        patient_info=PatientInfo(
            name="Original",
            dateOfBirth=946684800000,
            gender="M",
        )
    )
    ds = _FakeOrdersDataSource(existing)
    repo = OrdersRepository(ds)

    async def fake_fetch_patient(patient_id: str):
        if patient_id == "pat-2":
            return {
                "name": "Paciente Nuevo",
                "dateOfBirth": 946684800000,
                "gender": "F",
                "phone": "2",
                "address": "",
                "age": None,
            }
        return None

    patients = PatientsCollection.get_instance()
    monkeypatch.setattr(patients, "fetch_patient_by_id", fake_fetch_patient)

    updated = await repo.update_order_by_id(
        "ord-1",
        UpdateOrder(
            patientId="pat-2",
            patientInfo=PatientInfo(name="Alterado", dateOfBirth=0),
        ),
    )

    assert updated is not None
    assert updated.patientId == "pat-2"
    assert updated.patientInfo is not None
    assert updated.patientInfo.name == "Paciente Nuevo"
    assert ds.last_update is not None
    assert ds.last_update["patientInfo"]["name"] == "Paciente Nuevo"


@pytest.mark.asyncio
async def test_update_order_rejects_new_patient_without_demographics(
    monkeypatch,
) -> None:
    existing = _order(
        patient_info=PatientInfo(
            name="Original",
            dateOfBirth=946684800000,
            gender="M",
        )
    )
    ds = _FakeOrdersDataSource(existing)
    repo = OrdersRepository(ds)

    async def fake_fetch_patient(patient_id: str):
        return {
            "name": "Sin datos",
            "dateOfBirth": 0,
            "gender": "M",
            "phone": "3",
            "address": "",
            "age": None,
        }

    patients = PatientsCollection.get_instance()
    monkeypatch.setattr(patients, "fetch_patient_by_id", fake_fetch_patient)

    with pytest.raises(InvalidPatientDemographics):
        await repo.update_order_by_id("ord-1", UpdateOrder(patientId="pat-3"))


@pytest.mark.asyncio
async def test_update_order_fills_missing_snapshot_from_patient(monkeypatch) -> None:
    existing = _order(patient_info=None)
    ds = _FakeOrdersDataSource(existing)
    repo = OrdersRepository(ds)

    async def fake_fetch_patient(patient_id: str):
        return {
            "name": "Paciente Legacy",
            "dateOfBirth": 946684800000,
            "gender": "M",
            "phone": "4",
            "address": "",
            "age": None,
        }

    patients = PatientsCollection.get_instance()
    monkeypatch.setattr(patients, "fetch_patient_by_id", fake_fetch_patient)

    updated = await repo.update_order_by_id("ord-1", UpdateOrder(notes="Edición"))

    assert updated is not None
    assert updated.patientInfo is not None
    assert updated.patientInfo.name == "Paciente Legacy"
