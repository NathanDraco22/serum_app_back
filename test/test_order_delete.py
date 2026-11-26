import pytest
from fastapi import HTTPException

from app.api.v1.orders.orders_controller import OrdersController
from serum.core.exceptions import (
    CashShiftNotOpen,
    InsufficientMethodBalance,
    OrderCannotBeDeleted,
    OrderHasPayments,
)
from serum.core.order_payment import process_cancel_order as cancel_mod
from serum.core.reports.reports_pipelines import ReportsPipelines
from serum.repos.v1.common.models.user_info import UserInfo
from serum.repos.v1.orders.models.order_model import OrderInDb, OrderTestResult


class _FakeOrdersRepo:
    def __init__(self, order: OrderInDb) -> None:
        self.order = order
        self.cancelled_calls: list[dict] = []

    async def get_order_by_id(self, order_id: str) -> OrderInDb | None:
        return self.order if self.order.id == order_id else None

    async def cancel_order_by_id(
        self,
        order_id: str,
        cancelled_by=None,
        reason: str | None = None,
        extra_data: dict | None = None,
    ) -> OrderInDb | None:
        self.cancelled_calls.append(
            {
                "order_id": order_id,
                "cancelled_by": cancelled_by,
                "reason": reason,
                "extra_data": extra_data,
            }
        )
        return self.order.model_copy(
            update={
                "status": "cancelled",
                "isDeleted": True,
                "cancellationReason": reason,
            }
        )


class _FakeReceiptsRepo:
    def __init__(self, receipts: list | None = None) -> None:
        self.receipts = receipts or []

    async def get_all_receipts(self, filter_params=None) -> list:
        return self.receipts


def _make_order(
    *,
    status: str = "pending",
    paid_amount: int = 0,
    is_blocked: bool = False,
    is_deleted: bool = False,
    results: list[OrderTestResult] | None = None,
) -> OrderInDb:
    return OrderInDb(
        id="ord-1",
        patientId="pat-1",
        branchId="branch-1",
        totalPrice=10000,
        paidAmount=paid_amount,
        status=status,
        isBlocked=is_blocked,
        isDeleted=is_deleted,
        results=results or [],
        createdAt=1700000000000,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "is_blocked", "with_results"),
    [
        ("pending", False, False),
        ("pending", False, True),
        ("in_review", False, True),
        ("completed", False, True),
        ("pending", True, False),
    ],
)
async def test_delete_order_allowed_when_unpaid_and_not_cancelled(
    status: str,
    is_blocked: bool,
    with_results: bool,
) -> None:
    results = (
        [
            OrderTestResult(
                labTestId="t-1",
                parameterName="Glucosa",
                dataType="numeric",
                resultValue="95",
            )
        ]
        if with_results
        else []
    )
    order = _make_order(
        status=status,
        paid_amount=0,
        is_blocked=is_blocked,
        results=results,
    )
    orders_repo = _FakeOrdersRepo(order)
    controller = OrdersController(orders_repo=orders_repo)  # type: ignore[arg-type]
    controller.receipts_repo = _FakeReceiptsRepo([])  # type: ignore[assignment]

    cancelled = await controller.delete_order_by_id("ord-1", reason="Error de captura")

    assert cancelled.status == "cancelled"
    assert cancelled.isDeleted is True
    assert len(orders_repo.cancelled_calls) == 1


class _FakeOrderPaymentManager:
    def __init__(self, result_order: OrderInDb | None = None) -> None:
        self.result_order = result_order
        self.calls: list[dict] = []

    async def cancel_order_with_reversal(
        self,
        order_id: str,
        reason: str,
        cancelled_by=None,
    ) -> OrderInDb:
        self.calls.append(
            {
                "order_id": order_id,
                "reason": reason,
                "cancelled_by": cancelled_by,
            }
        )
        assert self.result_order is not None
        return self.result_order


@pytest.mark.asyncio
async def test_delete_order_with_payments_requires_reason() -> None:
    order = _make_order(status="pending", paid_amount=2500)
    orders_repo = _FakeOrdersRepo(order)
    controller = OrdersController(orders_repo=orders_repo)  # type: ignore[arg-type]
    controller.receipts_repo = _FakeReceiptsRepo([{"id": "rec-1"}])  # type: ignore[assignment]

    with pytest.raises(HTTPException) as exc_info:
        await controller.delete_order_by_id("ord-1", reason="   ")

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_delete_order_with_payments_delegates_to_reversal() -> None:
    order = _make_order(status="pending", paid_amount=2500)
    cancelled_result = _make_order(status="cancelled", paid_amount=0, is_deleted=True)
    orders_repo = _FakeOrdersRepo(order)
    payment_manager = _FakeOrderPaymentManager(result_order=cancelled_result)
    controller = OrdersController(orders_repo=orders_repo)  # type: ignore[arg-type]
    controller.receipts_repo = _FakeReceiptsRepo([{"id": "rec-1"}])  # type: ignore[assignment]
    controller.order_payment_manager = payment_manager  # type: ignore[assignment]

    cancelled = await controller.delete_order_by_id("ord-1", reason="Paciente canceló")

    assert cancelled.status == "cancelled"
    assert cancelled.isDeleted is True
    assert cancelled.paidAmount == 0
    assert len(payment_manager.calls) == 1
    assert payment_manager.calls[0]["reason"] == "Paciente canceló"


@pytest.mark.asyncio
async def test_delete_order_without_paid_amount_but_with_receipts_delegates_to_reversal() -> None:
    order = _make_order(status="pending", paid_amount=0)
    cancelled_result = _make_order(status="cancelled", paid_amount=0, is_deleted=True)
    orders_repo = _FakeOrdersRepo(order)
    payment_manager = _FakeOrderPaymentManager(result_order=cancelled_result)
    controller = OrdersController(orders_repo=orders_repo)  # type: ignore[arg-type]
    controller.receipts_repo = _FakeReceiptsRepo([{"id": "rec-1"}])  # type: ignore[assignment]
    controller.order_payment_manager = payment_manager  # type: ignore[assignment]

    cancelled = await controller.delete_order_by_id("ord-1", reason="Error de cobro")

    assert cancelled.status == "cancelled"
    assert len(payment_manager.calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "is_deleted"),
    [
        ("cancelled", False),
        ("pending", True),
    ],
)
async def test_delete_order_rejects_already_cancelled_or_deleted(
    status: str,
    is_deleted: bool,
) -> None:
    order = _make_order(status=status, paid_amount=0, is_deleted=is_deleted)
    orders_repo = _FakeOrdersRepo(order)
    controller = OrdersController(orders_repo=orders_repo)  # type: ignore[arg-type]
    controller.receipts_repo = _FakeReceiptsRepo([])  # type: ignore[assignment]

    with pytest.raises(OrderCannotBeDeleted):
        await controller.delete_order_by_id("ord-1")


class _AsyncNoopCtx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession(_AsyncNoopCtx):
    async def start_transaction(self):
        return _AsyncNoopCtx()

    def bind(self, end_session: bool = False):
        return _AsyncNoopCtx()


class _FakeMongoClient:
    def start_session(self):
        return _FakeSession()


class _FakeMongoService:
    def __init__(self) -> None:
        self.client = _FakeMongoClient()


class _FakeOrdersCol:
    def __init__(self, order_doc: dict | None) -> None:
        self.order_doc = order_doc
        self.cancelled_payload: dict | None = None

    async def fetch_order_by_id(self, order_id: str, session=None):
        return self.order_doc

    async def cancel_order_by_id(self, order_id: str, cancellation_data: dict, session=None):
        self.cancelled_payload = cancellation_data
        assert self.order_doc is not None
        return {**self.order_doc, **cancellation_data}


class _FakeReceiptsCol:
    def __init__(self, receipt_docs: list[dict]) -> None:
        self.receipt_docs = receipt_docs
        self.deleted_ids: list[str] = []

    async def fetch_all_receipts(self, filters=None, session=None):
        return self.receipt_docs

    async def delete_receipt_by_id(self, receipt_id: str, session=None, now=None):
        self.deleted_ids.append(receipt_id)
        return {"id": receipt_id, "isDeleted": True}


class _FakeShiftsCol:
    def __init__(self, shifts: dict[str, dict]) -> None:
        self.shifts = shifts
        self.balance_updates: list[tuple[str, str, int]] = []

    async def fetch_cash_shift_by_id(self, shift_id: str, session=None):
        return self.shifts.get(shift_id)

    async def add_to_balance(self, shift_id: str, payment_method: str, amount: int, session=None):
        self.balance_updates.append((shift_id, payment_method, amount))
        shift = self.shifts[shift_id]
        field = f"{payment_method}Balance"
        shift[field] = shift.get(field, 0) + amount
        shift["totalBalance"] = shift.get("totalBalance", 0) + amount
        return shift


class _FakeRegistersCol:
    async def fetch_cash_register_by_id(self, register_id: str, session=None):
        return None


class _FakeTransactionsCol:
    def __init__(self) -> None:
        self.created: list[dict] = []

    async def create_cash_transaction(self, tx: dict, session=None):
        self.created.append(tx)


def _patch_cancel_deps(
    monkeypatch,
    *,
    order_doc: dict,
    receipt_docs: list[dict],
    shifts: dict[str, dict],
):
    orders_col = _FakeOrdersCol(order_doc)
    receipts_col = _FakeReceiptsCol(receipt_docs)
    shifts_col = _FakeShiftsCol(shifts)
    registers_col = _FakeRegistersCol()
    tx_col = _FakeTransactionsCol()

    monkeypatch.setattr(cancel_mod, "MongoService", lambda: _FakeMongoService())
    monkeypatch.setattr(cancel_mod.OrdersCollection, "get_instance", lambda: orders_col)
    monkeypatch.setattr(cancel_mod.ReceiptsCollection, "get_instance", lambda: receipts_col)
    monkeypatch.setattr(cancel_mod.CashShiftsCollection, "get_instance", lambda: shifts_col)
    monkeypatch.setattr(cancel_mod.CashRegistersCollection, "get_instance", lambda: registers_col)
    monkeypatch.setattr(cancel_mod.CashTransactionsCollection, "get_instance", lambda: tx_col)
    return orders_col, receipts_col, shifts_col, tx_col


@pytest.mark.asyncio
async def test_process_cancel_order_reverts_open_shift_receipts_and_kardex(
    monkeypatch,
) -> None:
    order_doc = _make_order(status="in_review", paid_amount=10000).model_dump()
    receipt_docs = [
        {
            "id": "rec-1",
            "receiptNumber": "0001",
            "orderId": "ord-1",
            "branchId": "branch-1",
            "shiftId": "shift-1",
            "amount": 6000,
            "paymentMethod": "cash",
            "performedBy": {"id": "u-1", "name": "Cajero"},
            "createdAt": 1700000001000,
            "isDeleted": False,
        },
        {
            "id": "rec-2",
            "receiptNumber": "0002",
            "orderId": "ord-1",
            "branchId": "branch-1",
            "shiftId": "shift-1",
            "amount": 4000,
            "paymentMethod": "card",
            "performedBy": {"id": "u-1", "name": "Cajero"},
            "createdAt": 1700000002000,
            "isDeleted": False,
        },
    ]
    shifts = {
        "shift-1": {
            "id": "shift-1",
            "status": "OPEN",
            "initialBalance": 5000,
            "cashBalance": 6000,
            "cardBalance": 4000,
            "transferBalance": 0,
            "totalBalance": 15000,
        }
    }
    orders_col, receipts_col, shifts_col, tx_col = _patch_cancel_deps(
        monkeypatch, order_doc=order_doc, receipt_docs=receipt_docs, shifts=shifts
    )

    actor = UserInfo(id="u-2", name="Operador")
    result = await cancel_mod.process_cancel_order(
        order_id="ord-1",
        reason="Error en toma de muestra",
        cancelled_by=actor,
    )

    assert result.status == "cancelled"
    assert result.isDeleted is True
    assert result.paidAmount == 0
    assert result.cancellationReason == "Error en toma de muestra"
    assert receipts_col.deleted_ids == ["rec-1", "rec-2"]
    assert shifts_col.balance_updates == [
        ("shift-1", "cash", -6000),
        ("shift-1", "card", -4000),
    ]
    assert shifts["shift-1"]["cashBalance"] == 0
    assert shifts["shift-1"]["cardBalance"] == 0
    assert shifts["shift-1"]["totalBalance"] == 5000
    assert len(tx_col.created) == 2
    assert all(tx["flowType"] == "out" for tx in tx_col.created)
    assert all(tx["subType"] == "payment_reversal" for tx in tx_col.created)
    assert orders_col.cancelled_payload is not None
    assert orders_col.cancelled_payload["statusHistory"][-1]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_process_cancel_order_rejects_closed_shift(monkeypatch) -> None:
    order_doc = _make_order(status="pending", paid_amount=5000).model_dump()
    receipt_docs = [
        {
            "id": "rec-1",
            "orderId": "ord-1",
            "branchId": "branch-1",
            "shiftId": "shift-1",
            "amount": 5000,
            "paymentMethod": "cash",
            "performedBy": {"id": "u-1", "name": "Cajero"},
            "createdAt": 1700000001000,
            "isDeleted": False,
        }
    ]
    shifts = {
        "shift-1": {
            "id": "shift-1",
            "status": "CLOSED",
            "initialBalance": 5000,
            "cashBalance": 5000,
            "cardBalance": 0,
            "transferBalance": 0,
            "totalBalance": 10000,
        }
    }
    _, receipts_col, shifts_col, tx_col = _patch_cancel_deps(
        monkeypatch, order_doc=order_doc, receipt_docs=receipt_docs, shifts=shifts
    )

    with pytest.raises(CashShiftNotOpen):
        await cancel_mod.process_cancel_order(
            order_id="ord-1",
            reason="Cancelación tardía",
        )

    assert receipts_col.deleted_ids == []
    assert shifts_col.balance_updates == []
    assert tx_col.created == []


@pytest.mark.asyncio
async def test_process_cancel_order_rejects_insufficient_balance(monkeypatch) -> None:
    order_doc = _make_order(status="pending", paid_amount=5000).model_dump()
    receipt_docs = [
        {
            "id": "rec-1",
            "orderId": "ord-1",
            "branchId": "branch-1",
            "shiftId": "shift-1",
            "amount": 5000,
            "paymentMethod": "transfer",
            "performedBy": {"id": "u-1", "name": "Cajero"},
            "createdAt": 1700000001000,
            "isDeleted": False,
        }
    ]
    shifts = {
        "shift-1": {
            "id": "shift-1",
            "status": "OPEN",
            "initialBalance": 5000,
            "cashBalance": 5000,
            "cardBalance": 0,
            "transferBalance": 1000,
            "totalBalance": 11000,
        }
    }
    _, receipts_col, shifts_col, tx_col = _patch_cancel_deps(
        monkeypatch, order_doc=order_doc, receipt_docs=receipt_docs, shifts=shifts
    )

    with pytest.raises(InsufficientMethodBalance):
        await cancel_mod.process_cancel_order(
            order_id="ord-1",
            reason="Saldo insuficiente",
        )

    assert receipts_col.deleted_ids == []
    assert shifts_col.balance_updates == []
    assert tx_col.created == []


@pytest.mark.asyncio
async def test_process_cancel_order_rejects_paid_order_without_receipts(
    monkeypatch,
) -> None:
    order_doc = _make_order(status="pending", paid_amount=5000).model_dump()
    _patch_cancel_deps(
        monkeypatch, order_doc=order_doc, receipt_docs=[], shifts={}
    )

    with pytest.raises(OrderHasPayments):
        await cancel_mod.process_cancel_order(
            order_id="ord-1",
            reason="Sin recibos",
        )


@pytest.mark.asyncio
async def test_aggregate_cash_transactions_includes_payment_reversals() -> None:
    captured: dict = {}

    class _FakeCursor:
        async def to_list(self, length=None):
            return []

        async def close(self):
            return None

    class _FakeAggCollection:
        async def aggregate(self, pipeline):
            captured["pipeline"] = pipeline
            return _FakeCursor()

    await ReportsPipelines.aggregate_cash_transactions(
        _FakeAggCollection(),  # type: ignore[arg-type]
        start_date=100,
        end_date=200,
        branch_id="b-1",
    )

    pipeline = captured["pipeline"]
    match_stage = pipeline[0]["$match"]
    group_stage = pipeline[1]["$group"]
    assert {"flowType": "out", "subType": "payment_reversal"} in match_stage["$or"]
    assert "$cond" in group_stage["totalAmount"]["$sum"]
    assert "$cond" in group_stage["transactionsCount"]["$sum"]
