from serum.repos.v1.orders import OrderInDb


def with_legacy_status(order: OrderInDb) -> OrderInDb:
    """Devuelve una copia de la orden con el `status` financiero legacy calculado.

    La base de datos guarda únicamente el estado clínico (`pending`,
    `completed`, `cancelled`). Para no romper clientes antiguos que todavía
    leen `paid`/`partiallyPaid`, la respuesta HTTP calcula ese valor a partir
    de `paidAmount` y `totalPrice`. No se persiste.
    """

    if order.status in ("completed", "cancelled"):
        return order

    if order.totalPrice > 0 and order.paidAmount >= order.totalPrice:
        legacy_status = "paid"
    elif order.paidAmount > 0:
        legacy_status = "partiallyPaid"
    else:
        legacy_status = "pending"

    if legacy_status == order.status:
        return order

    return order.model_copy(update={"status": legacy_status})
