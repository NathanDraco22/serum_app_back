from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .models.order_model import OrderDiscount, OrderItem, OrderService


def _as_item_dict(item: OrderItem | dict[str, Any]) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    return item.model_dump()


def _as_service_dict(service: OrderService | dict[str, Any]) -> dict[str, Any]:
    if isinstance(service, dict):
        return service
    return service.model_dump()


def _as_discount_dict(discount: OrderDiscount | dict[str, Any]) -> dict[str, Any]:
    if isinstance(discount, dict):
        return discount
    return discount.model_dump()


def order_items_have_modified_price(
    items: list[OrderItem] | list[dict[str, Any]],
) -> bool:
    for raw_item in items:
        item = _as_item_dict(raw_item)
        original_price = int(item.get("originalPrice", 0) or 0)
        applied_price = int(item.get("salePriceApplied", 0) or 0)
        if original_price > 0 and applied_price != original_price:
            return True
    return False


def calculate_order_totals(
    items: list[OrderItem] | list[dict[str, Any]],
    services: list[OrderService] | list[dict[str, Any]],
    discounts: list[OrderDiscount] | list[dict[str, Any]],
) -> tuple[int, list[dict[str, Any]]]:
    """Calcula el total desde los componentes de la orden.

    El cliente puede seguir enviando ``totalPrice`` y ``appliedAmount`` para
    compatibilidad, pero el valor autoritativo se calcula aquí. Los descuentos
    porcentuales se recalculan con redondeo mitad hacia arriba para replicar el
    comportamiento de Dart. Los descuentos por monto conservan el
    ``appliedAmount`` explícito (la UI lo envía en centavos) y, si no viene,
    interpretan ``value`` como centavos por compatibilidad histórica.
    """

    gross_subtotal = sum(
        int(_as_item_dict(item).get("salePriceApplied", 0) or 0)
        for item in items
    )
    gross_subtotal += sum(
        int(_as_service_dict(service).get("price", 0) or 0)
        for service in services
    )

    processed_discounts: list[dict[str, Any]] = []
    discounts_total = 0

    for raw_discount in discounts:
        discount = dict(_as_discount_dict(raw_discount))
        discount_type = discount.get("type", "percentage")
        value = Decimal(str(discount.get("value", 0) or 0))

        if discount_type == "percentage":
            percentage = min(max(value, Decimal(0)), Decimal(100))
            applied = int(
                (Decimal(gross_subtotal) * percentage / Decimal(100)).quantize(
                    Decimal("1"), rounding=ROUND_HALF_UP
                )
            )
        else:
            existing_applied = int(discount.get("appliedAmount", 0) or 0)
            if existing_applied > 0:
                applied = existing_applied
            else:
                applied = int(
                    value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                )

        applied = max(0, min(applied, gross_subtotal))
        discount["appliedAmount"] = applied
        discounts_total += applied
        processed_discounts.append(discount)

    total = max(0, gross_subtotal - discounts_total)
    return total, processed_discounts
