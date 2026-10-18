from fastapi import HTTPException, Request, status
from serum.serum_config import SerumContext, serumCtx

EXEMPT_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
}


async def multi_tenant_middleware(req: Request):
    path = req.url.path

    # Rutas exentas de requerimiento de tenant (documentación, esquemas, etc.)
    if path in EXEMPT_PATHS or not path.startswith("/api/v1"):
        yield
        return

    tenant_nickname = req.headers.get("x-tenant-nickname") or req.headers.get(
        "x-servin"
    )
    branch_id = req.headers.get("x-branch") or req.headers.get("x-branch-id")

    if not tenant_nickname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required tenant header ('x-tenant-nickname' or 'X-Servin')",
        )

    new_ctx = SerumContext(
        businessNickname=tenant_nickname,
        branchId=branch_id or "",
    )

    token = serumCtx.set(new_ctx)
    try:
        yield
    finally:
        try:
            serumCtx.reset(token)
        except ValueError:
            pass

