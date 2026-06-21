from typing import TypeVar, Generic
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


class ListResponse(BaseModel, Generic[T]):
    count: int
    data: list[T]
