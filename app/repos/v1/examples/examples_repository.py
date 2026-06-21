from .data.examples_datasource import ExamplesDataSource
from .models.example_model import CreateExample, UpdateExample, ExampleInDb


class ExamplesRepository:
    def __init__(self, examples_ds: ExamplesDataSource):
        self.examples_ds = examples_ds

    async def create_example(self, create_example: CreateExample) -> ExampleInDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_examples(self) -> list[ExampleInDb]:
        results = await self.examples_ds.get_all_examples()
        models = [ExampleInDb.model_validate(result) for result in results]
        return models

    async def get_example_by_id(self, example_id: str) -> ExampleInDb | None :
        result = await self.examples_ds.get_example_by_id(example_id)
        
        if result is None:
            return None
        
        return ExampleInDb.model_validate(result)

    async def update_example_by_id(self, example_id: str, example: UpdateExample) -> ExampleInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_example_by_id(self, example_id: str) -> ExampleInDb | None:
        result = await self.examples_ds.delete_example_by_id(example_id)
        
        if result is None:
            return None
        
        return ExampleInDb.model_validate(result)
