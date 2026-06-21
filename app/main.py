import os
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from dotenv import load_dotenv
from api.v1.router import router_v1
from app_lifespan import lifespan

load_dotenv()

current_mode = os.getenv("MODE")
open_api_url = "/openapi.json"
if current_mode == "PROD":
    open_api_url = None

app = FastAPI(
    title="Server App",
    default_response_class=ORJSONResponse,
    openapi_url=open_api_url,
    lifespan=lifespan,
)

app.include_router(router_v1, prefix="/api/v1")
