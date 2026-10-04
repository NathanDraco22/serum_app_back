from fastapi import APIRouter

from .auths.auths_router import auths_router
from .branches.branches_router import branches_router
from .cash_registers.cash_registers_router import cash_registers_router
from .cash_shifts.cash_shifts_router import cash_shifts_router
from .cash_transactions.cash_transactions_router import cash_transactions_router
from .doctors.doctors_router import doctors_router
from .lab_tests.lab_tests_router import lab_tests_router
from .orders.orders_router import orders_router
from .patients.patients_router import patients_router
from .quotations.quotations_router import quotations_router
from .reports.reports_router import reports_router
from .roles.roles_router import roles_router
from .users.users_router import users_router

router_v1 = APIRouter(tags=["apiV1"])

router_v1.include_router(auths_router, prefix='/auths')
router_v1.include_router(branches_router, prefix="/branches")
router_v1.include_router(cash_registers_router, prefix="/cash-registers")
router_v1.include_router(cash_shifts_router, prefix='/cash-shifts')
router_v1.include_router(cash_transactions_router, prefix="/cash-transactions")
router_v1.include_router(doctors_router, prefix="/doctors")
router_v1.include_router(lab_tests_router, prefix="/lab-tests")
router_v1.include_router(orders_router, prefix="/orders")
router_v1.include_router(patients_router, prefix="/patients")
router_v1.include_router(quotations_router, prefix="/quotations")
router_v1.include_router(reports_router, prefix="/reports")
router_v1.include_router(roles_router, prefix='/roles')
router_v1.include_router(users_router, prefix="/users")

