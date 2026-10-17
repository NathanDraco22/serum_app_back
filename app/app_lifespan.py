from contextlib import asynccontextmanager

from fastapi import FastAPI

from serum.services_initializer import init_business_services


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_business_services()
    yield
