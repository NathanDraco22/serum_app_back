from typing import Literal

from pydantic import BaseModel, Field

from serum.repos.v1.common.models.user_info import UserInfo

PaymentMethodType = Literal["cash", "card", "transfer"]


class OpenCashRegisterRequest(BaseModel):
    initialCash: int = Field(ge=0)
    initialCard: int = Field(ge=0)
    initialTransfer: int = Field(ge=0)
    openedBy: UserInfo


class CloseCashRegisterRequest(BaseModel):
    performedBy: UserInfo


class IncomeRegisterRequest(BaseModel):
    amount: int = Field(gt=0)
    paymentMethod: PaymentMethodType
    concept: str
    performedBy: UserInfo


class WithdrawalRegisterRequest(BaseModel):
    amount: int = Field(gt=0)
    paymentMethod: PaymentMethodType
    concept: str
    performedBy: UserInfo


class PaymentRegisterRequest(BaseModel):
    amount: int = Field(gt=0)
    paymentMethod: PaymentMethodType
    orderId: str = Field(min_length=1)
    performedBy: UserInfo
