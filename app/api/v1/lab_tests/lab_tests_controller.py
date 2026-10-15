from fastapi import HTTPException, status
from core.lab_tests import LabTestsManager
from repos.v1.lab_test_accounts import (
    CreateLabTestAccount,
    LabTestAccountsRepository,
    LabTestCommercial,
    UpdateLabTestAccountCommercial,
)
from repos.v1.lab_tests import (
    CreateLabTest,
    LabTestInDb,
    LabTestsRepository,
    UpdateLabTest,
)
from responses.v1 import ListResponse


class LabTestsController:
    def __init__(self, lab_tests_repo: LabTestsRepository) -> None:
        self.lab_tests_repo = lab_tests_repo

    async def create_lab_test(self, body: CreateLabTest) -> LabTestInDb:
        return await LabTestsManager.get_instance().create_lab_test(body)

    async def get_all_lab_tests(
        self, branchId: str | None = None
    ) -> ListResponse[LabTestInDb]:
        lab_tests = await self.lab_tests_repo.get_all_lab_tests(branchId=branchId)
        return ListResponse(count=len(lab_tests), data=lab_tests)

    async def search_lab_test_by_text(
        self, text_query: str, branchId: str | None = None
    ) -> ListResponse[LabTestInDb]:
        lab_tests = await self.lab_tests_repo.search_lab_test_by_text(
            text_query, branchId=branchId
        )
        return ListResponse(count=len(lab_tests), data=lab_tests)

    async def get_lab_test_by_id(
        self, lab_test_id: str, branchId: str | None = None
    ) -> LabTestInDb:
        lab_test = await self.lab_tests_repo.get_lab_test_by_id(
            lab_test_id, branchId=branchId
        )
        if lab_test is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTest not found",
            )
        return lab_test

    async def update_lab_test_by_id(
        self, lab_test_id: str, body: UpdateLabTest
    ) -> LabTestInDb:
        updated_lab_test = await self.lab_tests_repo.update_lab_test_by_id(
            lab_test_id, body
        )
        if updated_lab_test is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTest not found",
            )

        # Sync commercial prices with LabTestAccount if commercial fields were modified
        if any(
            v is not None
            for v in (body.salePrice, body.salePrice2, body.costPrice, body.currency)
        ):
            branch_id = body.branchId or "ORIGIN_BRANCH"
            accounts_repo = LabTestAccountsRepository.get_instance()
            update_commercial = UpdateLabTestAccountCommercial(
                salePrice=body.salePrice,
                salePrice2=body.salePrice2,
                costPrice=body.costPrice,
                currency=body.currency,
            )
            account = await accounts_repo.update_commercial_by_branch_and_test(
                branchId=branch_id,
                labTestId=lab_test_id,
                update_model=update_commercial,
            )
            if account is None:
                account = await accounts_repo.create_account(
                    CreateLabTestAccount(
                        branchId=branch_id,
                        labTestId=lab_test_id,
                        commercial=LabTestCommercial(
                            salePrice=body.salePrice or updated_lab_test.salePrice,
                            salePrice2=body.salePrice2 or updated_lab_test.salePrice2,
                            costPrice=body.costPrice or updated_lab_test.costPrice,
                            currency=body.currency or updated_lab_test.currency,
                        ),
                    )
                )

            updated_lab_test.commercial = account.commercial
            if account.commercial.salePrice is not None:
                updated_lab_test.salePrice = account.commercial.salePrice
            if account.commercial.salePrice2 is not None:
                updated_lab_test.salePrice2 = account.commercial.salePrice2
            if account.commercial.costPrice is not None:
                updated_lab_test.costPrice = account.commercial.costPrice
            if account.commercial.currency is not None:
                updated_lab_test.currency = account.commercial.currency

        return updated_lab_test

    async def delete_lab_test_by_id(self, lab_test_id: str) -> LabTestInDb:
        deleted_lab_test = await self.lab_tests_repo.delete_lab_test_by_id(lab_test_id)
        if deleted_lab_test is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LabTest not found",
            )
        return deleted_lab_test


lab_tests_controller = LabTestsController(
    lab_tests_repo=LabTestsRepository.get_instance(),
)
