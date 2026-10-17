from pydantic import BaseModel
from serum.repos.v1.common.models.user_info import UserInfo


class OrderPayIntent(BaseModel):
    orderId: str
    amount: int
    shiftId: str | None = None
    registerId: str | None = None
    paymentMethod: str
    performedBy: UserInfo
