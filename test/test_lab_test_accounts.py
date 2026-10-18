import httpx
import pytest
from dotenv import load_dotenv

from serum.core.lab_tests import LabTestsManager
from serum.services_initializer import init_services
from main import app
from serum.repos.v1.branches import BranchesRepository, CreateBranch
from serum.repos.v1.lab_test_accounts import (
    LabTestAccountsRepository,
    UpdateLabTestAccountCommercial,
)
from serum.repos.v1.lab_tests import (
    CreateLabTest,
    LabTestsRepository,
)
from serum.services.mongo_collections.v1 import (
    BranchesCollection,
    LabTestAccountsCollection,
    LabTestsCollection,
)


@pytest.mark.asyncio
async def test_lab_test_accounts_and_core_process():
    load_dotenv("app/.env")
    await init_services()

    branches_col = BranchesCollection.get_instance()._collection
    lab_tests_col = LabTestsCollection.get_instance()._collection
    accounts_col = LabTestAccountsCollection.get_instance()._collection

    await branches_col.delete_many({})
    await lab_tests_col.delete_many({})
    await accounts_col.delete_many({})

    branches_repo = BranchesRepository.get_instance()
    lab_tests_repo = LabTestsRepository.get_instance()
    accounts_repo = LabTestAccountsRepository.get_instance()
    manager = LabTestsManager.get_instance()

    # 1. Setup 2 branches
    branch_1 = await branches_repo.create_branch(
        CreateBranch(name="Sucursal Norte", address="Calle 1", phone="111111")
    )
    branch_2 = await branches_repo.create_branch(
        CreateBranch(name="Sucursal Sur", address="Calle 2", phone="222222")
    )

    try:
        # 2. Create a LabTest targeting branch_1
        test_payload = CreateLabTest(
            name="Hemoglobina Glicosilada",
            commercialCategory="Química Clínica",
            branchId=branch_1.id,
            salePrice=25000,
            salePrice2=20000,
            costPrice=8000,
            currency="USD",
        )
        created_test = await manager.create_lab_test(test_payload)
        assert created_test.id is not None
        assert created_test.name == "Hemoglobina Glicosilada"

        # 3. Check LabTestAccount in branch_1
        acc_1 = await accounts_repo.get_by_branch_and_test(
            branch_1.id, created_test.id
        )
        assert acc_1 is not None
        assert acc_1.commercial.salePrice == 25000
        assert acc_1.commercial.salePrice2 == 20000
        assert acc_1.commercial.costPrice == 8000

        # 4. Check LabTestAccount in branch_2 (must be 0)
        acc_2 = await accounts_repo.get_by_branch_and_test(
            branch_2.id, created_test.id
        )
        assert acc_2 is not None
        assert acc_2.commercial.salePrice == 0
        assert acc_2.commercial.salePrice2 == 0
        assert acc_2.commercial.costPrice == 0

        # 5. Query tests for branch_1
        tests_b1 = await lab_tests_repo.get_all_lab_tests(branch_id=branch_1.id)
        t_b1 = next((t for t in tests_b1 if t.id == created_test.id), None)
        assert t_b1 is not None
        assert t_b1.salePrice == 25000
        assert t_b1.salePrice2 == 20000
        assert t_b1.costPrice == 8000
        assert t_b1.commercial is not None
        assert t_b1.commercial.salePrice == 25000

        # 6. Query tests for branch_2
        tests_b2 = await lab_tests_repo.get_all_lab_tests(branch_id=branch_2.id)
        t_b2 = next((t for t in tests_b2 if t.id == created_test.id), None)
        assert t_b2 is not None
        assert t_b2.salePrice == 0
        assert t_b2.salePrice2 == 0
        assert t_b2.costPrice == 0
        assert t_b2.commercial is not None
        assert t_b2.commercial.salePrice == 0

        # 7. Update commercial prices for branch_2 only
        updated_acc_2 = await accounts_repo.update_commercial(
            acc_2.id,
            UpdateLabTestAccountCommercial(
                salePrice=18000,
                salePrice2=15000,
                costPrice=7000,
            ),
        )
        assert updated_acc_2 is not None
        assert updated_acc_2.commercial.salePrice == 18000
        assert updated_acc_2.commercial.costPrice == 7000

        # Check that branch_1 remains unchanged
        acc_1_check = await accounts_repo.get_by_branch_and_test(
            branch_1.id, created_test.id
        )
        assert acc_1_check is not None
        assert acc_1_check.commercial.salePrice == 25000

        # 8. Create a brand new branch_3 and verify auto-provisioning
        branch_3 = await branches_repo.create_branch(
            CreateBranch(name="Sucursal Poniente", address="Calle 3", phone="333333")
        )
        acc_3 = await accounts_repo.get_by_branch_and_test(
            branch_3.id, created_test.id
        )
        assert acc_3 is not None
        assert acc_3.commercial.salePrice == 0
        assert acc_3.commercial.salePrice2 == 0
        assert acc_3.commercial.costPrice == 0

        # 9. Verify get_by_id and updatedAt
        acc_by_id = await accounts_repo.get_by_id(updated_acc_2.id)
        assert acc_by_id is not None
        assert acc_by_id.id == updated_acc_2.id
        assert acc_by_id.commercial.salePrice == 18000
        assert acc_by_id.updatedAt is not None

        # 10. Verify get_all with branchId and labTestId filters
        all_for_branch_2 = await accounts_repo.get_all(branchId=branch_2.id)
        assert any(a.id == updated_acc_2.id for a in all_for_branch_2)

        all_for_test = await accounts_repo.get_all(labTestId=created_test.id)
        assert len(all_for_test) >= 3

    finally:
        # Cleanup created records
        await branches_col.delete_many(
            {"id": {"$in": [branch_1.id, branch_2.id, "branch_3"]}}
        )
        await lab_tests_col.delete_many({"name": "Hemoglobina Glicosilada"})
        await accounts_col.delete_many(
            {"branchId": {"$in": [branch_1.id, branch_2.id]}}
        )


@pytest.mark.asyncio
async def test_lab_test_accounts_http_router():
    load_dotenv("app/.env")
    await init_services()

    branches_col = BranchesCollection.get_instance()._collection
    lab_tests_col = LabTestsCollection.get_instance()._collection
    accounts_col = LabTestAccountsCollection.get_instance()._collection

    branches_repo = BranchesRepository.get_instance()
    manager = LabTestsManager.get_instance()

    branch = await branches_repo.create_branch(
        CreateBranch(name="Sucursal Test HTTP", address="Calle HTTP", phone="999999")
    )
    test_model = await manager.create_lab_test(
        CreateLabTest(
            name="Glucosa en Suero Test HTTP",
            commercialCategory="Química",
            branchId=branch.id,
            salePrice=15000,
            salePrice2=12000,
            costPrice=5000,
        )
    )

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"X-Servin": "SerumDB"},
        ) as client:
            # 1. GET /api/v1/lab-test-accounts (filtro branchId)
            res_all = await client.get(
                "/api/v1/lab-test-accounts", params={"branchId": branch.id}
            )
            assert res_all.status_code == 200
            data_all = res_all.json()
            assert data_all["count"] >= 1
            account = next(
                a for a in data_all["data"] if a["labTestId"] == test_model.id
            )
            account_id = account["id"]
            assert account["commercial"]["salePrice"] == 15000

            # 2. GET /api/v1/lab-test-accounts/{account_id}
            res_by_id = await client.get(f"/api/v1/lab-test-accounts/{account_id}")
            assert res_by_id.status_code == 200
            assert res_by_id.json()["id"] == account_id

            # 3. PATCH /api/v1/lab-test-accounts/{account_id}/commercial
            res_patch = await client.patch(
                f"/api/v1/lab-test-accounts/{account_id}/commercial",
                json={"salePrice": 18500, "salePrice2": 16000},
            )
            assert res_patch.status_code == 200
            assert res_patch.json()["commercial"]["salePrice"] == 18500

            # 4. GET /api/v1/lab-test-accounts/{account_id} confirmando lectura actualizada
            res_by_id_after = await client.get(
                f"/api/v1/lab-test-accounts/{account_id}"
            )
            assert res_by_id_after.status_code == 200
            assert res_by_id_after.json()["commercial"]["salePrice"] == 18500
            assert res_by_id_after.json()["updatedAt"] is not None

            # 5. GET /api/v1/lab-tests?branchId=... (probar que camelCase branchId active el lookup)
            res_tests = await client.get(
                "/api/v1/lab-tests", params={"branchId": branch.id}
            )
            assert res_tests.status_code == 200
            matched_test = next(
                t for t in res_tests.json()["data"] if t["id"] == test_model.id
            )
            assert matched_test["salePrice"] == 18500
            assert matched_test["commercial"]["salePrice"] == 18500
    finally:
        await branches_col.delete_many({"id": branch.id})
        await lab_tests_col.delete_many({"id": test_model.id})
        await accounts_col.delete_many({"branchId": branch.id})
