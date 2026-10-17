from serum.core.exceptions import (
    CashMovementNotFound,
    CashShiftNotFound,
    CashShiftNotOpen,
    InsufficientMethodBalance,
)
from serum.repos.v1.cash_movements.models.cash_movement_model import CashMovementInDb
from serum.repos.v1.cash_transactions import CashTransactionInDb
from serum.services.mongo_service import MongoService
from serum.services.mongo_collections.v1 import (
    CashMovementsCollection,
    CashShiftsCollection,
    CashTransactionsCollection,
)
from serum.tools.time_tools import TimeTools
from serum.tools.uuid_tool import UuidTool


async def process_cancel_cash_movement(
    cash_movement_id: str,
) -> CashMovementInDb:
    mongo_client = MongoService().client
    shifts_col = CashShiftsCollection.get_instance()
    movements_col = CashMovementsCollection.get_instance()
    transactions_col = CashTransactionsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            async with session.bind(end_session=False):
                # 1. Obtener y validar el movimiento original
                movement_data = await movements_col.fetch_cash_movement_by_id(
                    cash_movement_id, session=session
                )
                if movement_data is None:
                    raise CashMovementNotFound()

                movement = CashMovementInDb.model_validate(movement_data)

                # 2. Obtener y validar el turno de caja
                shift_data = await shifts_col.fetch_cash_shift_by_id(
                    movement.shiftId, session=session
                )
                if shift_data is None:
                    raise CashShiftNotFound()

                if shift_data.get("status") != "OPEN":
                    raise CashShiftNotOpen()

                # 3. Pre-validación de fondos al revertir un ingreso
                # Si el movimiento original sumó dinero (income), anularlo equivale a retirarlo
                if movement.movementType == "income":
                    if movement.paymentMethod == "cash":
                        available_cash = shift_data.get(
                            "initialBalance", 0
                        ) + shift_data.get("cashBalance", 0)
                        if movement.amount > available_cash:
                            raise InsufficientMethodBalance()
                    else:
                        method_balance = shift_data.get(
                            f"{movement.paymentMethod}Balance", 0
                        )
                        if movement.amount > method_balance:
                            raise InsufficientMethodBalance()

                # Delta inverso: anular ingreso resta (-); anular egreso suma (+)
                delta_amount = (
                    -movement.amount
                    if movement.movementType == "income"
                    else movement.amount
                )

                # 4. Actualizar el saldo del turno atómicamente
                updated_shift = await shifts_col.add_to_balance(
                    shift_id=movement.shiftId,
                    payment_method=movement.paymentMethod,
                    amount=delta_amount,
                    session=session,
                )
                if updated_shift is None:
                    raise InsufficientMethodBalance()

                resulting_balance = updated_shift.get("totalBalance", 0)

                # 5. Marcar el movimiento como anulado (isDeleted = True)
                now = TimeTools.get_now_in_milliseconds()
                deleted_doc = await movements_col.delete_cash_movement_by_id(
                    cash_movement_id, session=session, now=now
                )
                if deleted_doc is None:
                    raise CashMovementNotFound()

                # 6. Registrar el contra-asiento compensatorio en el Kardex
                flow_type = (
                    "out" if movement.movementType == "income" else "in"
                )
                reversal_prefix = (
                    "Anulación de ingreso libre"
                    if movement.movementType == "income"
                    else "Anulación de egreso libre"
                )
                contra_sub_type = (
                    "withdrawal" if movement.movementType == "income" else "income"
                )

                transaction = CashTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    shiftId=movement.shiftId,
                    registerId=movement.registerId,
                    branchId=movement.branchId,
                    flowType=flow_type,
                    subType=contra_sub_type,
                    paymentMethod=movement.paymentMethod,
                    amount=movement.amount,
                    resultingBalance=resulting_balance,
                    concept=f"[{reversal_prefix}] {movement.concept}",
                    referenceId=movement.id,
                    performedBy=movement.performedBy,
                    createdAt=now,
                    updatedAt=None,
                    isDeleted=False,
                )

                await transactions_col.create_cash_transaction(
                    transaction.model_dump(), session=session
                )

                return CashMovementInDb.model_validate(deleted_doc)
