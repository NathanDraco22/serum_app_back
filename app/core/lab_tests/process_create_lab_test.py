from repos.v1.branches import BranchesRepository
from repos.v1.lab_test_accounts import (
    CreateLabTestAccount,
    LabTestAccountsRepository,
    LabTestCommercial,
)
from repos.v1.lab_tests import CreateLabTest, LabTestInDb, LabTestsRepository
from services.mongo_service import MongoService


async def process_create_lab_test(create_data: CreateLabTest) -> LabTestInDb:
    mongo_client = MongoService().client
    lab_tests_repo = LabTestsRepository.get_instance()
    accounts_repo = LabTestAccountsRepository.get_instance()
    branches_repo = BranchesRepository.get_instance()

    target_branch_id = create_data.branchId
    sale_price = create_data.salePrice
    sale_price2 = create_data.salePrice2
    cost_price = create_data.costPrice
    currency = create_data.currency

    # Fetch all active branches
    branches = await branches_repo.get_all_branches()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind(end_session=False):
                # 1. Create the master LabTest
                created_test = await lab_tests_repo.create_lab_test(
                    create_data, session=session
                )

                # 2. Prepare accounts for all branches
                accounts_to_create: list[CreateLabTestAccount] = []

                # Origin branch account
                origin_commercial = LabTestCommercial(
                    salePrice=sale_price,
                    salePrice2=sale_price2,
                    costPrice=cost_price,
                    currency=currency,
                )
                accounts_to_create.append(
                    CreateLabTestAccount(
                        branchId=target_branch_id,
                        labTestId=created_test.id,
                        commercial=origin_commercial,
                    )
                )

                # Other branches accounts (initialized to 0)
                for branch in branches:
                    if branch.id != target_branch_id:
                        accounts_to_create.append(
                            CreateLabTestAccount(
                                branchId=branch.id,
                                labTestId=created_test.id,
                                commercial=LabTestCommercial(
                                    salePrice=0,
                                    salePrice2=0,
                                    costPrice=0,
                                    currency=currency,
                                ),
                            )
                        )

                # 3. Batch insert accounts
                await accounts_repo.create_accounts_batch(
                    accounts_to_create, session=session
                )

                # Attach origin commercial to returned model
                created_test.commercial = origin_commercial
                created_test.costPrice = cost_price
                return created_test
