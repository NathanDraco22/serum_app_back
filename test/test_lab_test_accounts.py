import pytest
from dotenv import load_dotenv

from core.lab_tests import LabTestsManager
from core.services_initializer import init_services
from repos.v1.branches import BranchesRepository, CreateBranch
from repos.v1.lab_test_accounts import (
    LabTestAccountsRepository,
    UpdateLabTestAccountCommercial,
)
from repos.v1.lab_tests import (
    CreateLabTest,
    LabTestsRepository,
)
from services.mongo_collections.v1 import (
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

    finally:
        # Cleanup created records
        await branches_col.delete_many(
            {"id": {"$in": [branch_1.id, branch_2.id, "branch_3"]}}
        )
        await lab_tests_col.delete_many({"name": "Hemoglobina Glicosilada"})
        await accounts_col.delete_many(
            {"branchId": {"$in": [branch_1.id, branch_2.id]}}
        )
