from fastapi import APIRouter

from repos.v1.quotations import CreateQuotation, QuotationInDb, UpdateQuotation
from responses.v1 import ListResponse

from .quotations_controller import quotations_controller

quotations_router = APIRouter(tags=["quotationsV1"])


@quotations_router.post("")
async def create_quotation(body: CreateQuotation) -> QuotationInDb:
    return await quotations_controller.create_quotation(body)


@quotations_router.get("")
async def get_all_quotations() -> ListResponse[QuotationInDb]:
    return await quotations_controller.get_all_quotations()


@quotations_router.get("/{quotation_id}")
async def get_quotation_by_id(quotation_id: str) -> QuotationInDb:
    return await quotations_controller.get_quotation_by_id(quotation_id)


@quotations_router.patch("/{quotation_id}")
async def update_quotation_by_id(
    quotation_id: str, body: UpdateQuotation
) -> QuotationInDb:
    return await quotations_controller.update_quotation_by_id(quotation_id, body)


@quotations_router.delete("/{quotation_id}")
async def delete_quotation_by_id(quotation_id: str) -> QuotationInDb:
    return await quotations_controller.delete_quotation_by_id(quotation_id)
