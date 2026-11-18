import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

from app.api.v1.imports.imports_controller import ImportsController
from serum.core.default_values import ORIGIN_BRANCH_ID, import_new_lab_tests
from serum.repos.v1.branches import BranchesRepository
from serum.repos.v1.lab_test_accounts import (
    CreateLabTestAccount,
    LabTestAccountsRepository,
)
from serum.repos.v1.lab_tests import CreateLabTest, LabTestInDb, LabTestsRepository


class _FakeLabTestsRepo:
    def __init__(self, initial: list[LabTestInDb] | None = None) -> None:
        self.items: list[LabTestInDb] = list(initial or [])
        self.updated_calls: list[tuple[str, object]] = []
        self._seq = len(self.items)

    async def get_all_lab_tests(self) -> list[LabTestInDb]:
        return list(self.items)

    async def create_lab_tests_batch(
        self, dtos: list[CreateLabTest]
    ) -> list[LabTestInDb]:
        created: list[LabTestInDb] = []
        for dto in dtos:
            self._seq += 1
            data = dto.model_dump(exclude={"branchId"})
            item = LabTestInDb(
                id=f"lt-{self._seq}",
                createdAt=1,
                **data,
            )
            self.items.append(item)
            created.append(item)
        return created

    async def update_lab_test_by_id(self, test_id: str, update_dto: object) -> None:
        self.updated_calls.append((test_id, update_dto))


class _FakeAccountsRepo:
    def __init__(self) -> None:
        self.created_accounts: list[CreateLabTestAccount] = []

    async def create_accounts_batch(
        self, accounts: list[CreateLabTestAccount]
    ) -> None:
        self.created_accounts.extend(accounts)


class _FakeBranchesRepo:
    def __init__(self, branch_ids: list[str]) -> None:
        self._branches = [SimpleNamespace(id=bid, name=bid) for bid in branch_ids]

    async def get_all_branches(self) -> list[SimpleNamespace]:
        return self._branches


def _patch_repos(
    monkeypatch: pytest.MonkeyPatch,
    *,
    initial_tests: list[LabTestInDb] | None = None,
    branch_ids: list[str] | None = None,
) -> tuple[_FakeLabTestsRepo, _FakeAccountsRepo]:
    fake_tests = _FakeLabTestsRepo(initial_tests)
    fake_accounts = _FakeAccountsRepo()
    fake_branches = _FakeBranchesRepo(branch_ids or [ORIGIN_BRANCH_ID, "branch-2"])

    monkeypatch.setattr(LabTestsRepository, "get_instance", lambda: fake_tests)
    monkeypatch.setattr(
        LabTestAccountsRepository, "get_instance", lambda: fake_accounts
    )
    monkeypatch.setattr(BranchesRepository, "get_instance", lambda: fake_branches)
    return fake_tests, fake_accounts


@pytest.mark.asyncio
async def test_import_new_lab_tests_imports_atopica_panel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_tests, fake_accounts = _patch_repos(monkeypatch)
    import_path = (
        Path(__file__).resolve().parents[2]
        / "lab_test_procesor"
        / "backup"
        / "panel_atopica_30i_import.json"
    )
    items = json.loads(import_path.read_text(encoding="utf-8"))

    result = await import_new_lab_tests(items)

    assert result.success is True
    assert result.atomicCreated == 30
    assert result.packsCreated == 1
    assert result.alreadyExisting == 0
    assert result.totalProcessed == 31
    assert result.accountsCreated == 62  # 31 pruebas * 2 sucursales
    assert len(fake_accounts.created_accounts) == 62
    assert fake_tests.updated_calls == []

    pack = next(t for t in fake_tests.items if t.code == "PANEL-ATOP30I")
    assert pack.isPack is True
    assert len(pack.childTestIds) == 30
    assert pack.childTestIds[0] == "lt-1"
    assert pack.childTestIds[-1] == "lt-30"


@pytest.mark.asyncio
async def test_import_new_lab_tests_never_overwrites_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = LabTestInDb(
        id="existing-1",
        name="f02 Leche (Personalizada)",
        code="ALG-F02",
        commercialCategory="Inmunología",
        salePrice=5000,
        createdAt=1,
    )
    fake_tests, fake_accounts = _patch_repos(
        monkeypatch,
        initial_tests=[existing],
        branch_ids=[ORIGIN_BRANCH_ID],
    )

    items = [
        {
            "name": "f02 Leche",
            "code": "ALG-F02",
            "commercialCategory": "Inmunología",
            "salePrice": 0,
            "isPack": False,
            "dataType": "numeric",
            "unitOfMeasure": "kU/L",
        },
        {
            "name": "f76 α-Lactoalbúmina",
            "code": "ALG-F76",
            "commercialCategory": "Inmunología",
            "salePrice": 0,
            "isPack": False,
            "dataType": "numeric",
            "unitOfMeasure": "kU/L",
        },
        {
            "name": "Mini Pack Alergia",
            "code": "MINI-ALG",
            "commercialCategory": "Inmunología",
            "salePrice": 0,
            "isPack": True,
            "childTestCodes": ["ALG-F02", "ALG-F76"],
            "dataType": "qualitative",
        },
    ]

    result = await import_new_lab_tests(items)

    assert result.success is True
    assert result.atomicCreated == 1
    assert result.packsCreated == 1
    assert result.alreadyExisting == 1
    assert result.skippedCodes == ["ALG-F02"]
    assert fake_tests.updated_calls == []
    assert fake_tests.items[0].name == "f02 Leche (Personalizada)"
    assert fake_tests.items[0].salePrice == 5000
    assert len(fake_accounts.created_accounts) == 2

    pack = next(t for t in fake_tests.items if t.code == "MINI-ALG")
    assert pack.childTestIds == ["existing-1", "lt-2"]


@pytest.mark.asyncio
async def test_controller_import_file_and_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_repos(monkeypatch, branch_ids=[ORIGIN_BRANCH_ID])
    controller = ImportsController()

    valid_bytes = json.dumps(
        [
            {
                "name": "Prueba Nueva",
                "code": "NEW-01",
                "commercialCategory": "Inmunología",
                "isPack": False,
                "dataType": "numeric",
                "unitOfMeasure": "kU/L",
            }
        ]
    ).encode("utf-8")
    upload = UploadFile(filename="new.json", file=io.BytesIO(valid_bytes))

    res = await controller.import_new_lab_tests_file(upload)
    assert res.success is True
    assert res.atomicCreated == 1

    bad_upload = UploadFile(filename="bad.json", file=io.BytesIO(b"{invalid"))
    with pytest.raises(HTTPException) as exc_info:
        await controller.import_new_lab_tests_file(bad_upload)
    assert exc_info.value.status_code == 400

    obj_upload = UploadFile(filename="obj.json", file=io.BytesIO(b'{"a": 1}'))
    with pytest.raises(HTTPException) as exc_obj:
        await controller.import_new_lab_tests_file(obj_upload)
    assert exc_obj.value.status_code == 400

    with pytest.raises(HTTPException) as exc_empty:
        await controller.import_new_lab_tests_json([])
    assert exc_empty.value.status_code == 400
