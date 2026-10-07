from typing import Any

from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool
from core.exceptions import (
    CashShiftAlreadyOpen,
    CashShiftAlreadyClosed,
    CashShiftNotFound,
)

from .data.cash_shifts_datasource import CashShiftsDataSource
from .models.cash_shift_model import (
    CloseCashShift,
    CreateCashShift,
    UpdateCashShift,
    CashShiftInDb,
)


class CashShiftsRepository:
    _instance: "CashShiftsRepository|None" = None

    def __init__(self, cash_shifts_ds: CashShiftsDataSource):
        self.cash_shifts_ds = cash_shifts_ds

    @classmethod
    def get_instance(cls) -> "CashShiftsRepository":
        if cls._instance is None:
            cls._instance = cls(CashShiftsDataSource())
        return cls._instance

    async def _resolve_names(
        self, user_id: str, branch_id: str
    ) -> tuple[str | None, str | None]:
        user_name = None
        branch_name = None
        try:
            from services.mongo_collections.v1 import (
                BranchesCollection,
                UsersCollection,
            )

            users_col = UsersCollection.get_instance()._collection
            user_doc = await users_col.find_one(
                {"id": user_id, "isDeleted": {"$ne": True}},
                {"name": 1, "fullName": 1, "username": 1},
            )
            if user_doc:
                user_name = (
                    user_doc.get("name")
                    or user_doc.get("fullName")
                    or user_doc.get("username")
                )

            branches_col = BranchesCollection.get_instance()._collection
            branch_doc = await branches_col.find_one(
                {"id": branch_id, "isDeleted": {"$ne": True}}, {"name": 1}
            )
            if branch_doc:
                branch_name = branch_doc.get("name")
        except Exception:
            pass
        return user_name, branch_name

    async def _enrich_shifts(self, shifts_data: list[dict[str, Any]]) -> None:
        missing_users = {
            s.get("userId")
            for s in shifts_data
            if not s.get("userName") and s.get("userId")
        }
        missing_branches = {
            s.get("branchId")
            for s in shifts_data
            if not s.get("branchName") and s.get("branchId")
        }

        users_map: dict[str, str] = {}
        branches_map: dict[str, str] = {}

        if missing_users:
            try:
                from services.mongo_collections.v1 import UsersCollection

                users_col = UsersCollection.get_instance()._collection
                cursor = users_col.find(
                    {
                        "id": {"$in": list(missing_users)},
                        "isDeleted": {"$ne": True},
                    },
                    {"id": 1, "name": 1, "fullName": 1, "username": 1},
                )
                users = await cursor.to_list(length=None)
                await cursor.close()
                users_map = {
                    u["id"]: u.get("name")
                    or u.get("fullName")
                    or u.get("username", "Usuario")
                    for u in users
                }
            except Exception:
                pass

        if missing_branches:
            try:
                from services.mongo_collections.v1 import BranchesCollection

                branches_col = BranchesCollection.get_instance()._collection
                cursor = branches_col.find(
                    {
                        "id": {"$in": list(missing_branches)},
                        "isDeleted": {"$ne": True},
                    },
                    {"id": 1, "name": 1},
                )
                branches = await cursor.to_list(length=None)
                await cursor.close()
                branches_map = {
                    b["id"]: b.get("name", "Sucursal") for b in branches
                }
            except Exception:
                pass

        for s in shifts_data:
            if not s.get("userName") and s.get("userId") in users_map:
                s["userName"] = users_map[s["userId"]]
            if not s.get("branchName") and s.get("branchId") in branches_map:
                s["branchName"] = branches_map[s["branchId"]]

    async def open_shift(self, create_cash_shift: CreateCashShift) -> CashShiftInDb:
        existing = await self.cash_shifts_ds.get_active_shift_by_user(
            create_cash_shift.userId
        )
        if existing is not None:
            raise CashShiftAlreadyOpen()

        user_name = create_cash_shift.userName
        branch_name = create_cash_shift.branchName
        if not user_name or not branch_name:
            res_u, res_b = await self._resolve_names(
                create_cash_shift.userId, create_cash_shift.branchId
            )
            user_name = user_name or res_u
            branch_name = branch_name or res_b

        now = TimeTools.get_now_in_milliseconds()
        new_shift = CashShiftInDb(
            id=UuidTool.generate_uuid(),
            userId=create_cash_shift.userId,
            branchId=create_cash_shift.branchId,
            notes=create_cash_shift.notes,
            userName=user_name,
            branchName=branch_name,
            status="OPEN",
            openedAt=now,
            closedAt=None,
            initialBalance=create_cash_shift.initialBalance,
            cashBalance=0,
            cardBalance=0,
            transferBalance=0,
            totalBalance=create_cash_shift.initialBalance,
            declaredCash=None,
            difference=None,
            isDeleted=False,
            createdAt=now,
            updatedAt=None,
        )

        result = await self.cash_shifts_ds.create_cash_shift(new_shift.model_dump())
        return CashShiftInDb.model_validate(result)

    async def get_current_shift(self, user_id: str) -> CashShiftInDb | None:
        result = await self.cash_shifts_ds.get_active_shift_by_user(user_id)
        if result is None:
            return None
        await self._enrich_shifts([result])
        return CashShiftInDb.model_validate(result)

    async def close_shift(
        self,
        shift_id: str,
        close_data: CloseCashShift,
        user_id: str | None = None,
    ) -> CashShiftInDb:
        result = await self.cash_shifts_ds.get_cash_shift_by_id(shift_id)
        if result is None:
            raise CashShiftNotFound()

        shift = CashShiftInDb.model_validate(result)
        if user_id is not None and shift.userId != user_id:
            raise CashShiftNotFound()

        if shift.status != "OPEN":
            raise CashShiftAlreadyClosed()

        diff = close_data.declaredCash - (shift.initialBalance + shift.cashBalance)
        now = TimeTools.get_now_in_milliseconds()

        update_dict: dict[str, Any] = {
            "status": "CLOSED",
            "closedAt": now,
            "declaredCash": close_data.declaredCash,
            "difference": diff,
            "updatedAt": now,
        }
        if close_data.notes:
            update_dict["notes"] = close_data.notes

        updated = await self.cash_shifts_ds.update_cash_shift_by_id(
            shift_id, update_dict
        )
        if updated is None:
            raise CashShiftNotFound()

        await self._enrich_shifts([updated])
        return CashShiftInDb.model_validate(updated)

    async def get_all_cash_shifts(
        self,
        branch_id: str | None = None,
        user_id: str | None = None,
        status: str | None = None,
    ) -> list[CashShiftInDb]:
        filter_dict: dict[str, Any] = {}
        if branch_id:
            filter_dict["branchId"] = branch_id
        if user_id:
            filter_dict["userId"] = user_id
        if status:
            filter_dict["status"] = status

        results = await self.cash_shifts_ds.get_all_cash_shifts(
            filter_dict if filter_dict else None
        )
        await self._enrich_shifts(results)
        return [CashShiftInDb.model_validate(result) for result in results]

    async def get_cash_shift_by_id(self, cash_shift_id: str) -> CashShiftInDb | None:
        result = await self.cash_shifts_ds.get_cash_shift_by_id(cash_shift_id)
        if result is None:
            return None
        await self._enrich_shifts([result])
        return CashShiftInDb.model_validate(result)

    async def update_cash_shift_by_id(
        self, cash_shift_id: str, cash_shift: UpdateCashShift
    ) -> CashShiftInDb | None:
        update_data = cash_shift.model_dump(exclude_unset=True)
        update_data["updatedAt"] = TimeTools.get_now_in_milliseconds()
        result = await self.cash_shifts_ds.update_cash_shift_by_id(
            cash_shift_id, update_data
        )
        if result is None:
            return None
        return CashShiftInDb.model_validate(result)

    async def delete_cash_shift_by_id(
        self, cash_shift_id: str
    ) -> CashShiftInDb | None:
        result = await self.cash_shifts_ds.delete_cash_shift_by_id(cash_shift_id)
        if result is None:
            return None
        return CashShiftInDb.model_validate(result)
