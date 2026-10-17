from serum.core.exceptions import (
    CashShiftNotFound,
    CashShiftNotOpen,
    ConceptRequired,
    InsufficientMethodBalance,
    InvalidAmount,
    InvalidMovementType,
    InvalidPaymentMethod,
)
from serum.repos.v1.cash_movements.models.cash_movement_model import (
    CashMovementInDb,
    CreateCashMovement,
)
from serum.repos.v1.cash_transactions import CashTransactionInDb
from serum.services.mongo_service import MongoService
from serum.services.mongo_collections.v1 import (
    CashMovementsCollection,
    CashShiftsCollection,
    CashTransactionsCollection,
)
from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool


async def process_cash_movement(
    create_movement: CreateCashMovement,
) -> CashMovementInDb:
    if create_movement.movementType not in ("income", "withdrawal"):
        raise InvalidMovementType()

    if create_movement.amount <= 0:
        raise InvalidAmount()

    if not create_movement.concept or not create_movement.concept.strip():
        raise ConceptRequired()

    if create_movement.paymentMethod not in ("cash", "card", "transfer"):
        raise InvalidPaymentMethod()

    mongo_client = MongoService().client
    shifts_col = CashShiftsCollection.get_instance()
    movements_col = CashMovementsCollection.get_instance()
    transactions_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind(end_session=False):
                shift_data = await shifts_col.fetch_cash_shift_by_id(
                    create_movement.shiftId, session=session
                )
                if shift_data is None:
                    raise CashShiftNotFound()

                if shift_data.get("status") != "OPEN":
                    raise CashShiftNotOpen()

                branch_id = create_movement.branchId or shift_data.get(
                    "branchId", ""
                )
                resolved_register_id = (
                    create_movement.registerId or shift_data.get("registerId")
                )

                # Pre-validación de fondos para egreso / retiro
                if create_movement.movementType == "withdrawal":
                    if create_movement.paymentMethod == "cash":
                        available_cash = shift_data.get(
                            "initialBalance", 0
                        ) + shift_data.get("cashBalance", 0)
                        if create_movement.amount > available_cash:
                            raise InsufficientMethodBalance()
                    else:
                        method_balance = shift_data.get(
                            f"{create_movement.paymentMethod}Balance", 0
                        )
                        if create_movement.amount > method_balance:
                            raise InsufficientMethodBalance()

                delta_amount = (
                    create_movement.amount
                    if create_movement.movementType == "income"
                    else -create_movement.amount
                )

                updated_shift = await shifts_col.add_to_balance(
                    shift_id=create_movement.shiftId,
                    payment_method=create_movement.paymentMethod,
                    amount=delta_amount,
                    session=session,
                )
                if updated_shift is None:
                    raise InsufficientMethodBalance()

                resulting_balance = updated_shift.get("totalBalance", 0)

                now = TimeTools.get_now_in_milliseconds()
                movement_id = UuidTool.generate_uuid()

                movement = CashMovementInDb(
                    id=movement_id,
                    shiftId=create_movement.shiftId,
                    branchId=branch_id,
                    movementType=create_movement.movementType,
                    paymentMethod=create_movement.paymentMethod,
                    amount=create_movement.amount,
                    concept=create_movement.concept.strip(),
                    performedBy=create_movement.performedBy,
                    resultingBalance=resulting_balance,
                    registerId=resolved_register_id,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await movements_col.create_cash_movement(
                    movement.model_dump(), session=session
                )

                flow_type = (
                    "in" if create_movement.movementType == "income" else "out"
                )
                concept_prefix = (
                    "Ingreso libre"
                    if create_movement.movementType == "income"
                    else "Egreso libre"
                )

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    shiftId=create_movement.shiftId,
                    registerId=resolved_register_id,
                    branchId=branch_id,
                    flowType=flow_type,
                    subType=create_movement.movementType,
                    paymentMethod=create_movement.paymentMethod,
                    amount=create_movement.amount,
                    resultingBalance=resulting_balance,
                    concept=f"[{concept_prefix}] {create_movement.concept.strip()}",
                    referenceId=movement_id,
                    performedBy=create_movement.performedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transactions_col.create_cash_transaction(
                    transaction.model_dump(), session=session
                )

                return movement
