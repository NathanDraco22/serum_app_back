from typing import Any


class ExamplesDataSource:
    async def create_example(self, example: dict[str, Any]) -> dict[str, Any]:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_examples(self) -> list[dict[str, Any]]:
        # TODO: implement get all
        raise NotImplementedError()

    async def get_example_by_id(self, example_id: str) -> dict[str, Any] | None :
        # TODO: implement get by id
        raise NotImplementedError()

    async def update_example_by_id(self, example_id:str, example:dict[str, Any]) -> dict[str, Any] | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_example_by_id(self, example_id:str) -> dict[str, Any] | None:
        # TODO: implement delete
        raise NotImplementedError()
