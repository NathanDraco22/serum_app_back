import pytest
from app.datasource.v1.my_datasource import MyDatasource


def test_demo():
    assert (2+2) == 4


@pytest.mark.asyncio
async def test_my_datasource():
    my_ds = MyDatasource()
    assert (await my_ds.get_data()) == "Hello, World"