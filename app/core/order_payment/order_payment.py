from pydantic import BaseModel
from repos.v1.common.models.user_info import UserInfo


class OrderPayIntent(BaseModel):
    orderId: str
    amount: int
    registerId: str
    paymentMethod: str
    performedBy: UserInfo
