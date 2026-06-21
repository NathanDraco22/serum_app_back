from fastapi import APIRouter

from repos.v1.examples import CreateExample, UpdateExample, ExampleInDb

from .examples_controller import examples_controller


examples_router = APIRouter(tags=["examplesV1"])


@examples_router.post("")
async def create_example_endpoint(body: CreateExample) -> ExampleInDb:
    return await examples_controller.create_example(body)


@examples_router.get("")
async def get_all_examples_endpoint() -> list[ExampleInDb]:
    return await examples_controller.get_all_examples()


@examples_router.get("/{example_id}")
async def get_example_by_id_endpoint(example_id: str) -> ExampleInDb:
    return await examples_controller.get_example_by_id(example_id)


@examples_router.patch("/{example_id}")
async def update_example_by_id_endpoint(
    example_id: str, body: UpdateExample
) -> ExampleInDb:
    return await examples_controller.update_example_by_id(example_id, body)


@examples_router.delete("/{example_id}")
async def delete_example_by_id_endpoint(example_id: str) -> ExampleInDb:
    return await examples_controller.delete_example_by_id(example_id)
