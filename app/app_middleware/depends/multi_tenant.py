from fastapi import Request
from serum.serum_config import SerumContext, serumCtx


async def multi_tenant_middleware(req: Request):
    tenant_nickname = req.headers.get("X-Servin")
    branch_id = req.headers.get("x-branch-id")

    new_ctx = SerumContext(
        businessNickname=tenant_nickname or "",
        branchId=branch_id or "",
    )

    token = serumCtx.set(new_ctx)
    try:
        yield
    finally:
        serumCtx.reset(token)
