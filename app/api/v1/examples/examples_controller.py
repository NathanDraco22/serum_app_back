from fastapi import HTTPException, status

from repos.v1.examples import (
    CreateExample, 
    UpdateExample, 
    ExampleInDb, 
    ExamplesRepository,
    ExamplesDataSource,
)


class ExamplesController:
    def __init__(self, examples_repo: ExamplesRepository) -> None:
        self.examples_repo = examples_repo

    async def create_example(self, body: CreateExample) -> ExampleInDb:
        return await self.examples_repo.create_example(body)

    async def get_all_examples(self) -> list[ExampleInDb]:
        examples = await self.examples_repo.get_all_examples()
        return examples

    async def get_example_by_id(self, example_id: str) -> ExampleInDb:
        example = await self.examples_repo.get_example_by_id(example_id)
        if example is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Example not found",
            )
        return example

    async def update_example_by_id(self, example_id: str, body: UpdateExample) -> ExampleInDb:
        updated_example = await self.examples_repo.update_example_by_id(example_id, body)
        if updated_example is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Example not found",
            )
        return updated_example

    async def delete_example_by_id(self, example_id: str) -> ExampleInDb:
        deleted_example = await self.examples_repo.delete_example_by_id(example_id)
        if deleted_example is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Example not found",
            )
        return deleted_example

examples_controller = ExamplesController(
    examples_repo=ExamplesRepository(
        examples_ds=ExamplesDataSource(),
    ),
)
