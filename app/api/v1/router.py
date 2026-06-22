from fastapi import APIRouter

from .users.users_router import users_router

router_v1 = APIRouter(tags=["apiV1"])

router_v1.include_router(users_router, prefix="/users")
