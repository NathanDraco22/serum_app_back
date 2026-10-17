from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from serum.core.security import TokenManager

header_schema = APIKeyHeader(name="Authorization", auto_error=True)


async def validate_super_token(token: str = Depends(header_schema)):
    res = TokenManager.super_token_verify(token)

    if res is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return res
