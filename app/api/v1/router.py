from fastapi import APIRouter

from .examples.examples_router import examples_router

router_v1 = APIRouter(tags=["apiV1"])

router_v1.include_router(examples_router, prefix="/examples")
