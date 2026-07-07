from pydantic import BaseModel


class BaseFilterParams(BaseModel):
    offset: int = 0
    limit: int = 50
