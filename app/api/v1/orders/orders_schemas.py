from typing import Literal

from pydantic import BaseModel, Field

from serum.repos.v1.common.models.user_info import UserInfo


class OrderPayRequest(BaseModel):
    amount: int = Field(gt=0)
    shiftId: str | None = None
    registerId: str | None = None
    paymentMethod: Literal["cash", "card", "transfer"]
    performedBy: UserInfo


class OrderApproveRequest(BaseModel):
    supervisorUsername: str | None = None
    supervisorPassword: str | None = None
    approvedBy: UserInfo | None = None
    reason: str = "Aprobado por supervisor"
