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
    # 1. Petición con x-tenant-nickname y x-branch-id
    scope = {
        "type": "http",
        "path": "/api/v1/patients",
        "headers": [
            (b"x-tenant-nickname", b"lab_central"),
            (b"x-branch-id", b"branch_norte"),
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

    # 2. Petición con x-servin como nickname
    scope_servin = {
        "type": "http",
        "path": "/api/v1/patients",
        "headers": [
            (b"x-servin", b"clinica_del_sol"),
            (b"x-branch", b"branch_matriz"),
        ],
    }
    req_servin = Request(scope_servin)
    gen2 = multi_tenant_middleware(req_servin)
    await anext(gen2)
    assert serumCtx.get().businessNickname == "clinica_del_sol"
    assert serumCtx.get().branchId == "branch_matriz"
    try:
        await anext(gen2)
    except StopAsyncIteration:
        pass

    # 3. Petición sin header a /api/v1 debe arrojar 400 Bad Request
    scope_no_tenant = {
        "type": "http",
        "path": "/api/v1/patients",
        "headers": [],
    }
    req_no_tenant = Request(scope_no_tenant)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        gen3 = multi_tenant_middleware(req_no_tenant)
        await anext(gen3)
    assert exc_info.value.status_code == 400


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
        # 1. Sin tenant -> default DB ("SerumDB")
        serumCtx.set(SerumContext(businessNickname="", branchId=""))
        res1 = mongo.get_collection("Patients")
        assert res1 == ("SerumDB", "Patients")

        # 2. Con tenant -> nickname directo
        serumCtx.set(SerumContext(businessNickname="clinica_sur", branchId="b1"))
        res2 = mongo.get_collection("Patients")
        assert res2 == ("clinica_sur", "Patients")
    finally:
        serumCtx.set(SerumContext())
        if original_client:
            mongo.client = original_client


def test_collection_instances_isolation():
    from serum.services.mongo_collections.v1 import (
        PatientsCollection,
        OrdersCollection,
    )

    # 1. Instancias separadas para distintos tenants
    pat_a = PatientsCollection.get_instance("lab_a")
    pat_b = PatientsCollection.get_instance("lab_b")
    assert pat_a is not pat_b
    assert pat_a.nickname == "lab_a"
    assert pat_b.nickname == "lab_b"

    # 2. Misma instancia (cacheada) para el mismo tenant
    pat_a_again = PatientsCollection.get_instance("lab_a")
    assert pat_a is pat_a_again

    # 3. Aislamiento entre distintas subclases
    order_a = OrdersCollection.get_instance("lab_a")
    assert pat_a is not order_a
    assert "lab_a" in PatientsCollection._instances
    assert "lab_a" in OrdersCollection._instances
    assert isinstance(PatientsCollection._instances["lab_a"], PatientsCollection)
    assert isinstance(OrdersCollection._instances["lab_a"], OrdersCollection)

