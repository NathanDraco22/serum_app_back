from pydantic import BaseModel


class BaseExample(BaseModel):
    pass


class CreateExample(BaseExample):
    pass


class UpdateExample(BaseModel):
    pass


class ExampleInDb(BaseExample):
    id: str
    created_at: str
    updated_at: str
