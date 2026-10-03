from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from core.exceptions import (
    CashRegisterAlreadyOpen,
    CashRegisterNotFound,
    CashRegisterNotOpen,
    CashRegisterAlreadyClosed,
    ConceptRequired,
    InsufficientMethodBalance,
    InvalidPaymentMethod,
    OrderNotFound,
    OrderAlreadyPaid,
    CashShiftAlreadyOpen,
    CashShiftNotFound,
    CashShiftNotOpen,
    CashShiftAlreadyClosed,
)


async def handle_cash_register_already_open_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, CashRegisterAlreadyOpen) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "CASH_REGISTER_ALREADY_OPEN"},
    )


async def handle_cash_register_not_found_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, CashRegisterNotFound) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "CASH_REGISTER_NOT_FOUND"},
    )


async def handle_cash_register_not_open_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, CashRegisterNotOpen) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "CASH_REGISTER_NOT_OPEN"},
    )


async def handle_cash_register_already_closed_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, CashRegisterAlreadyClosed) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "CASH_REGISTER_ALREADY_CLOSED"},
    )


async def handle_concept_required_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, ConceptRequired) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "CONCEPT_REQUIRED"},
    )


async def handle_insufficient_method_balance_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, InsufficientMethodBalance) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "INSUFFICIENT_METHOD_BALANCE"},
    )


async def handle_invalid_payment_method_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, InvalidPaymentMethod) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "INVALID_PAYMENT_METHOD"},
    )


async def handle_order_not_found_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, OrderNotFound) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "ORDER_NOT_FOUND"},
    )


async def handle_order_already_paid_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, OrderAlreadyPaid) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "ORDER_NOT_PAYABLE"},
    )


async def handle_cash_shift_already_open_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, CashShiftAlreadyOpen) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "CASH_SHIFT_ALREADY_OPEN"},
    )


async def handle_cash_shift_not_found_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, CashShiftNotFound) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "CASH_SHIFT_NOT_FOUND"},
    )


async def handle_cash_shift_not_open_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, CashShiftNotOpen) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "CASH_SHIFT_NOT_OPEN"},
    )


async def handle_cash_shift_already_closed_exception(request: Request, exc: Exception):
    res = exc if isinstance(exc, CashShiftAlreadyClosed) else None
    if res is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "INTERNAL_SERVER_ERROR_EXCEPTION"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "CASH_SHIFT_ALREADY_CLOSED"},
    )


_exceptions_handlers = {
    CashRegisterAlreadyOpen: handle_cash_register_already_open_exception,
    CashRegisterNotFound: handle_cash_register_not_found_exception,
    CashRegisterNotOpen: handle_cash_register_not_open_exception,
    CashRegisterAlreadyClosed: handle_cash_register_already_closed_exception,
    ConceptRequired: handle_concept_required_exception,
    InsufficientMethodBalance: handle_insufficient_method_balance_exception,
    InvalidPaymentMethod: handle_invalid_payment_method_exception,
    OrderNotFound: handle_order_not_found_exception,
    OrderAlreadyPaid: handle_order_already_paid_exception,
    CashShiftAlreadyOpen: handle_cash_shift_already_open_exception,
    CashShiftNotFound: handle_cash_shift_not_found_exception,
    CashShiftNotOpen: handle_cash_shift_not_open_exception,
    CashShiftAlreadyClosed: handle_cash_shift_already_closed_exception,
}


def register_exception_handlers(app: FastAPI):
    for exc_class, handler in _exceptions_handlers.items():
        app.add_exception_handler(exc_class, handler)
