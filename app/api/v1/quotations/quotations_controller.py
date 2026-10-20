from fastapi import HTTPException, status
from serum.serum_config import serumCtx

from serum.repos.v1.common.filter_params import QuotationFilterParams
from serum.repos.v1.quotations import (
    CreateQuotation,
    QuotationInDb,
    QuotationsRepository,
    UpdateQuotation,
)
from responses.v1 import ListResponse


class QuotationsController:
    def __init__(self, quotations_repo: QuotationsRepository) -> None:
        self.quotations_repo = quotations_repo

    async def create_quotation(self, body: CreateQuotation) -> QuotationInDb:
        return await self.quotations_repo.create_quotation(body)

    async def get_all_quotations(
        self, query_params: QuotationFilterParams | None = None
    ) -> ListResponse[QuotationInDb]:
        if query_params is None:
            query_params = QuotationFilterParams()
        if query_params.branchId is None and serumCtx.get().branchId:
            query_params.branchId = serumCtx.get().branchId

        quotations = await self.quotations_repo.get_all_quotations(query_params)
        return ListResponse(count=len(quotations), data=quotations)

    async def get_quotation_by_id(self, quotation_id: str) -> QuotationInDb:
        quotation = await self.quotations_repo.get_quotation_by_id(quotation_id)
        if quotation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quotation not found",
            )
        return quotation

    async def update_quotation_by_id(
        self, quotation_id: str, body: UpdateQuotation
    ) -> QuotationInDb:
        updated_quotation = await self.quotations_repo.update_quotation_by_id(
            quotation_id, body
        )
        if updated_quotation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quotation not found",
            )
        return updated_quotation

    async def delete_quotation_by_id(self, quotation_id: str) -> QuotationInDb:
        deleted_quotation = await self.quotations_repo.delete_quotation_by_id(
            quotation_id
        )
        if deleted_quotation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quotation not found",
            )
        return deleted_quotation


quotations_controller = QuotationsController(
    quotations_repo=QuotationsRepository.get_instance(),
)
