import pytest

from app.api.v1.orders.orders_controller import OrdersController
from serum.core.exceptions import OrderCannotBeDeleted, OrderHasPayments
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


@pytest.mark.asyncio
async def test_delete_order_rejects_when_paid_amount_positive() -> None:
    order = _make_order(status="pending", paid_amount=2500)
    orders_repo = _FakeOrdersRepo(order)
    controller = OrdersController(orders_repo=orders_repo)  # type: ignore[arg-type]
    controller.receipts_repo = _FakeReceiptsRepo([])  # type: ignore[assignment]

    with pytest.raises(OrderHasPayments):
        await controller.delete_order_by_id("ord-1")


@pytest.mark.asyncio
async def test_delete_order_rejects_when_receipts_exist() -> None:
    order = _make_order(status="pending", paid_amount=0)
    orders_repo = _FakeOrdersRepo(order)
    controller = OrdersController(orders_repo=orders_repo)  # type: ignore[arg-type]
    controller.receipts_repo = _FakeReceiptsRepo([{"id": "rec-1"}])  # type: ignore[assignment]

    with pytest.raises(OrderHasPayments):
        await controller.delete_order_by_id("ord-1")


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
