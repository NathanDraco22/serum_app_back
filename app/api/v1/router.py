from fastapi import APIRouter

from .users.users_router import users_router
from .branches.branches_router import branches_router
from .patients.patients_router import patients_router
from .doctors.doctors_router import doctors_router

router_v1 = APIRouter(tags=["apiV1"])

router_v1.include_router(users_router, prefix="/users")
router_v1.include_router(branches_router, prefix="/branches")
router_v1.include_router(patients_router, prefix="/patients")
router_v1.include_router(doctors_router, prefix="/doctors")
