from serum.core.default_values.create_default_branch import ORIGIN_BRANCH_ID
from serum.repos.v1.cash_registers.models.cash_register_model import CashRegisterInDb
from serum.services.mongo_collections.v1.cash_registers_collection import CashRegistersCollection
from serum.tools.time_tools import TimeTools

ORIGIN_CASH_ID = "ORIGIN_CASH"
ORIGIN_CASH = "ORIGIN_CASH"
ORIGIN_CASH_NAME = "Caja Principal"


async def create_default_cash_register(
    cash_register_name: str | None = None,
    branch_id: str = ORIGIN_BRANCH_ID,
) -> CashRegisterInDb:
    target_cash_name = (
        cash_register_name if cash_register_name is not None else ORIGIN_CASH_NAME
    )
    new_cash_register = CashRegisterInDb(
        id=ORIGIN_CASH_ID,
        branchId=branch_id,
        name=target_cash_name,
        isOpen=False,
        cashBalance=0,
        cardBalance=0,
        transferBalance=0,
        totalBalance=0,
        openedBy=None,
        createdAt=TimeTools.get_now_in_milliseconds(),
        isDeleted=False,
    )

    await CashRegistersCollection.get_instance().create_cash_register_if_absent(
        ORIGIN_CASH_ID, new_cash_register.model_dump()
    )

    return new_cash_register
