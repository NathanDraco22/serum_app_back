import pytest
from dotenv import load_dotenv

from serum.core.exceptions import (
    CashMovementNotFound,
    CashShiftNotFound,
    CashShiftNotOpen,
    ConceptRequired,
    InsufficientMethodBalance,
    InvalidAmount,
    InvalidMovementType,
)
from serum.core.cash_movements import CashMovementManager
from serum.services_initializer import init_services
from serum.repos.v1.branches import BranchesRepository, CreateBranch
from serum.repos.v1.cash_movements import (
    CashMovementsRepository,
    CreateCashMovement,
    UpdateCashMovement,
)
from serum.repos.v1.cash_shifts import CashShiftsRepository, CreateCashShift
from serum.repos.v1.common.filter_params import CashMovementFilterParams
from serum.repos.v1.common.models.user_info import UserInfo
from serum.services.mongo_collections.v1 import (
    BranchesCollection,
    CashMovementsCollection,
    CashShiftsCollection,
    CashTransactionsCollection,
    CountersCollection,
)


@pytest.mark.asyncio
async def test_cash_movements_flow_and_kardex_impact():
    load_dotenv("app/.env")
    await init_services()

    # Reset test collections
    await CashMovementsCollection.get_instance()._collection.delete_many({})
    await CashShiftsCollection.get_instance()._collection.delete_many({})
    await CashTransactionsCollection.get_instance()._collection.delete_many({})
    await BranchesCollection.get_instance()._collection.delete_many({})
    await CountersCollection.get_instance()._collection.delete_many({})

    # Setup branch and open a shift
    branch = await BranchesRepository.get_instance().create_branch(
        CreateBranch(name="Sucursal Centro", address="Calle Principal 100", phone="555-1111")
    )
    user_info = UserInfo(id="user-cajero-1", name="Carlos Cajero")

    # Shift opens with 50000 cents ($500.00 MXN) initial balance
    shift = await CashShiftsRepository.get_instance().open_shift(
        CreateCashShift(
            userId=user_info.id,
            userName=user_info.name,
            branchId=branch.id,
            initialBalance=50000,
        )
    )
    assert shift.status == "OPEN"
    assert shift.initialBalance == 50000
    assert shift.cashBalance == 0
    assert shift.totalBalance == 50000

    repo = CashMovementsRepository.get_instance()
    mgr = CashMovementManager()

    # 1. Test Income (Ingreso libre)
    income_mov = await mgr.process_movement(
        CreateCashMovement(
            shiftId=shift.id,
            branchId=branch.id,
            movementType="income",
            paymentMethod="cash",
            amount=20000,  # $200.00 MXN
            concept="Fondo adicional para cambio",
            performedBy=user_info,
        )
    )
    assert income_mov.id is not None
    assert income_mov.amount == 20000
    assert income_mov.movementType == "income"
    assert income_mov.concept == "Fondo adicional para cambio"
    assert income_mov.resultingBalance == 70000

    # Verify shift balance updated
    updated_shift = await CashShiftsRepository.get_instance().get_cash_shift_by_id(shift.id)
    assert updated_shift is not None
    assert updated_shift.cashBalance == 20000
    assert updated_shift.totalBalance == 70000

    # Verify Kardex CashTransaction created
    txs = await CashTransactionsCollection.get_instance().fetch_all_cash_transactions(
        {"shiftId": shift.id}
    )
    # 1 opening tx + 1 income tx
    assert len(txs) == 2
    income_tx = next(t for t in txs if t.get("subType") == "income")
    assert income_tx["flowType"] == "in"
    assert income_tx["amount"] == 20000
    assert income_tx["referenceId"] == income_mov.id
    assert income_tx["resultingBalance"] == 70000
    assert "[Ingreso libre]" in income_tx["concept"]

    # 2. Test Withdrawal with Insufficient Funds
    # Total cash in drawer is 50000 (initial) + 20000 (income) = 70000 cents.
    # Trying to withdraw 80000 must fail with InsufficientMethodBalance
    with pytest.raises(InsufficientMethodBalance):
        await mgr.process_movement(
            CreateCashMovement(
                shiftId=shift.id,
                branchId=branch.id,
                movementType="withdrawal",
                paymentMethod="cash",
                amount=80000,
                concept="Retiro excesivo no permitido",
                performedBy=user_info,
            )
        )

    # 3. Test Successful Withdrawal (Egreso libre)
    withdraw_mov = await mgr.process_movement(
        CreateCashMovement(
            shiftId=shift.id,
            branchId=branch.id,
            movementType="withdrawal",
            paymentMethod="cash",
            amount=15000,  # $150.00 MXN
            concept="Pago de garrafón de agua y café",
            performedBy=user_info,
        )
    )
    assert withdraw_mov.amount == 15000
    assert withdraw_mov.movementType == "withdrawal"
    assert withdraw_mov.resultingBalance == 55000

    # Verify shift balance updated
    updated_shift_2 = await CashShiftsRepository.get_instance().get_cash_shift_by_id(shift.id)
    assert updated_shift_2 is not None
    assert updated_shift_2.cashBalance == 5000
    assert updated_shift_2.totalBalance == 55000

    # Verify Kardex CashTransaction for withdrawal
    txs_after = await CashTransactionsCollection.get_instance().fetch_all_cash_transactions(
        {"shiftId": shift.id}
    )
    assert len(txs_after) == 3
    withdraw_tx = next(t for t in txs_after if t.get("subType") == "withdrawal")
    assert withdraw_tx["flowType"] == "out"
    assert withdraw_tx["amount"] == 15000
    assert withdraw_tx["referenceId"] == withdraw_mov.id
    assert withdraw_tx["resultingBalance"] == 55000
    assert "[Egreso libre]" in withdraw_tx["concept"]

    # 4. Validations
    # Invalid movementType
    with pytest.raises(InvalidMovementType):
        await mgr.process_movement(
            CreateCashMovement(
                shiftId=shift.id,
                branchId=branch.id,
                movementType="unknown",
                paymentMethod="cash",
                amount=5000,
                concept="Concepto",
                performedBy=user_info,
            )
        )

    # Non-positive amount
    with pytest.raises(InvalidAmount):
        await mgr.process_movement(
            CreateCashMovement(
                shiftId=shift.id,
                branchId=branch.id,
                movementType="income",
                paymentMethod="cash",
                amount=0,
                concept="Concepto",
                performedBy=user_info,
            )
        )

    # Empty concept
    with pytest.raises(ConceptRequired):
        await mgr.process_movement(
            CreateCashMovement(
                shiftId=shift.id,
                branchId=branch.id,
                movementType="income",
                paymentMethod="cash",
                amount=1000,
                concept="   ",
                performedBy=user_info,
            )
        )

    # Non-existent shift
    with pytest.raises(CashShiftNotFound):
        await mgr.process_movement(
            CreateCashMovement(
                shiftId="non-existent-shift",
                branchId=branch.id,
                movementType="income",
                paymentMethod="cash",
                amount=1000,
                concept="Concepto",
                performedBy=user_info,
            )
        )

    # Closed shift validation
    closed_shift = await CashShiftsRepository.get_instance().open_shift(
        CreateCashShift(
            userId="user-closed",
            userName="User Closed",
            branchId=branch.id,
            initialBalance=10000,
        )
    )
    from serum.repos.v1.cash_shifts.models.cash_shift_model import CloseCashShift
    await CashShiftsRepository.get_instance().close_shift(
        closed_shift.id,
        CloseCashShift(declaredCash=10000),
    )
    with pytest.raises(CashShiftNotOpen):
        await mgr.process_movement(
            CreateCashMovement(
                shiftId=closed_shift.id,
                branchId=branch.id,
                movementType="income",
                paymentMethod="cash",
                amount=1000,
                concept="Concepto",
                performedBy=user_info,
            )
        )

    # 5. Query Filters
    incomes = await repo.get_all_cash_movements(
        CashMovementFilterParams(shiftId=shift.id, movementType="income")
    )
    assert len(incomes) == 1
    assert incomes[0].id == income_mov.id

    withdrawals = await repo.get_all_cash_movements(
        CashMovementFilterParams(shiftId=shift.id, movementType="withdrawal")
    )
    assert len(withdrawals) == 1
    assert withdrawals[0].id == withdraw_mov.id

    # 6. Update Concept
    updated = await repo.update_cash_movement_by_id(
        withdraw_mov.id,
        UpdateCashMovement(concept="Pago de 2 garrafones de agua y café"),
    )
    assert updated is not None
    assert updated.concept == "Pago de 2 garrafones de agua y café"
    assert updated.amount == 15000  # Amount immutable

    # 7. Atomic Cancellation of Withdrawal (Egreso) with Balance Reversal
    # Current shift balance before cancel: cashBalance=5000, totalBalance=55000
    mgr = CashMovementManager()
    cancelled_withdraw = await mgr.cancel_movement(withdraw_mov.id)
    assert cancelled_withdraw.id == withdraw_mov.id
    assert cancelled_withdraw.isDeleted is True

    # Shift balance must be restored (+15000)
    shift_after_cancel = await CashShiftsRepository.get_instance().get_cash_shift_by_id(shift.id)
    assert shift_after_cancel is not None
    assert shift_after_cancel.cashBalance == 20000
    assert shift_after_cancel.totalBalance == 70000

    # Kardex counter-entry must be recorded
    txs_after_cancel = await CashTransactionsCollection.get_instance().fetch_all_cash_transactions(
        {"shiftId": shift.id}
    )
    # 1 opening + 1 income + 1 withdrawal + 1 reversal withdrawal
    assert len(txs_after_cancel) == 4
    reversal_tx = txs_after_cancel[0]  # newest first
    assert "[Anulación de egreso libre]" in reversal_tx["concept"]
    assert reversal_tx["flowType"] == "in"
    assert reversal_tx["amount"] == 15000
    assert reversal_tx["resultingBalance"] == 70000

    # Cannot cancel twice
    with pytest.raises(CashMovementNotFound):
        await mgr.cancel_movement(withdraw_mov.id)

    # 8. Atomic Cancellation of Income (Ingreso) with Balance Reversal
    cancelled_income = await mgr.cancel_movement(income_mov.id)
    assert cancelled_income.isDeleted is True

    shift_after_income_cancel = await CashShiftsRepository.get_instance().get_cash_shift_by_id(shift.id)
    assert shift_after_income_cancel is not None
    assert shift_after_income_cancel.cashBalance == 0
    assert shift_after_income_cancel.totalBalance == 50000

    txs_after_income_cancel = await CashTransactionsCollection.get_instance().fetch_all_cash_transactions(
        {"shiftId": shift.id}
    )
    assert len(txs_after_income_cancel) == 5
    income_reversal_tx = txs_after_income_cancel[0]
    assert "[Anulación de ingreso libre]" in income_reversal_tx["concept"]
    assert income_reversal_tx["flowType"] == "out"
    assert income_reversal_tx["amount"] == 20000
    assert income_reversal_tx["resultingBalance"] == 50000

