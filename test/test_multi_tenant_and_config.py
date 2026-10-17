import asyncio
import pytest
from fastapi import Request
from serum.serum_config import SerumConfig, SerumContext, serumCtx
from serum.services import MongoService
from app_middleware.depends.multi_tenant import multi_tenant_middleware


def test_serum_config_singleton():
    cfg1 = SerumConfig()
    cfg2 = SerumConfig()
    assert cfg1 is cfg2


@pytest.mark.asyncio
async def test_serum_context_isolation_across_async_tasks():
    # Context should default to empty
    assert serumCtx.get().businessNickname == ""
    assert serumCtx.get().branchId == ""

    async def task_a():
        token = serumCtx.set(SerumContext(businessNickname="tenant_a", branchId="branch_a"))
        try:
            await asyncio.sleep(0.01)
            ctx = serumCtx.get()
            assert ctx.businessNickname == "tenant_a"
            assert ctx.branchId == "branch_a"
        finally:
            serumCtx.reset(token)

    async def task_b():
        token = serumCtx.set(SerumContext(businessNickname="tenant_b", branchId="branch_b"))
        try:
            await asyncio.sleep(0.01)
            ctx = serumCtx.get()
            assert ctx.businessNickname == "tenant_b"
            assert ctx.branchId == "branch_b"
        finally:
            serumCtx.reset(token)

    await asyncio.gather(task_a(), task_b())

    # After tasks, parent context remains clean
    assert serumCtx.get().businessNickname == ""
    assert serumCtx.get().branchId == ""


@pytest.mark.asyncio
async def test_multi_tenant_middleware():
    scope = {
        "type": "http",
        "headers": [
            (b"x-tenant-nickname", b"lab_central"),
            (b"x-servin", b"branch_norte"),
        ],
    }
    request = Request(scope)

    # Before middleware
    assert serumCtx.get().businessNickname == ""
    assert serumCtx.get().branchId == ""

    # Execute middleware generator
    gen = multi_tenant_middleware(request)
    await anext(gen)

    # Inside request lifecycle
    ctx = serumCtx.get()
    assert ctx.businessNickname == "lab_central"
    assert ctx.branchId == "branch_norte"

    # After request lifecycle (finally)
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass

    assert serumCtx.get().businessNickname == ""
    assert serumCtx.get().branchId == ""


def test_mongo_service_dynamic_db_resolution():
    mongo = MongoService()
    # Fake client to check db name
    class FakeClient:
        def __init__(self):
            self.requested_dbs = []
        def get_database(self, name):
            self.requested_dbs.append(name)
            class FakeDB:
                def get_collection(self, cname):
                    return (name, cname)
            return FakeDB()

    original_client = getattr(mongo, "client", None)
    fake_client = FakeClient()
    mongo.client = fake_client  # type: ignore

    try:
        # 1. Sin tenant -> default DB
        serumCtx.set(SerumContext(businessNickname="", branchId=""))
        res1 = mongo.get_collection("Patients")
        assert res1 == ("SerumDB", "Patients")

        # 2. Con tenant -> SerumDB_<tenant>
        serumCtx.set(SerumContext(businessNickname="clinica_sur", branchId="b1"))
        res2 = mongo.get_collection("Patients")
        assert res2 == ("SerumDB_clinica_sur", "Patients")
    finally:
        serumCtx.set(SerumContext())
        if original_client:
            mongo.client = original_client
