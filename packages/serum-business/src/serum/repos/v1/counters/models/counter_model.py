from pydantic import BaseModel


class CounterInDb(BaseModel):
    name: str
    value: int
