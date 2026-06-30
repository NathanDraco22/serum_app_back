from tools.uuid_tool import UuidTool
from tools.time_tools import TimeTools

from .data.quotations_datasource import QuotationsDataSource
from .models.quotation_model import CreateQuotation, UpdateQuotation, QuotationInDb


class QuotationsRepository:

    _instance: "QuotationsRepository|None" = None

    def __init__(self, quotations_ds: QuotationsDataSource):
        self.quotations_ds = quotations_ds

    @classmethod
    def get_instance(cls) -> "QuotationsRepository":
        if cls._instance is None:
            cls._instance = cls(QuotationsDataSource())
        return cls._instance

    async def create_quotation(self, create_quotation: CreateQuotation) -> QuotationInDb:
        new_quotation = QuotationInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_quotation.model_dump(),
        )
        result = await self.quotations_ds.create_quotation(new_quotation.model_dump())
        return QuotationInDb.model_validate(result)

    async def get_all_quotations(self) -> list[QuotationInDb]:
        results = await self.quotations_ds.get_all_quotations()
        return [QuotationInDb.model_validate(r) for r in results]

    async def get_quotation_by_id(self, quotation_id: str) -> QuotationInDb | None:
        result = await self.quotations_ds.get_quotation_by_id(quotation_id)
        if result is None:
            return None
        return QuotationInDb.model_validate(result)

    async def update_quotation_by_id(self, quotation_id: str, quotation: UpdateQuotation) -> QuotationInDb | None:
        updated_data = quotation.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.quotations_ds.update_quotation_by_id(quotation_id, updated_data)
        if result is None:
            return None
        return QuotationInDb.model_validate(result)

    async def delete_quotation_by_id(self, quotation_id: str) -> QuotationInDb | None:
        result = await self.quotations_ds.delete_quotation_by_id(quotation_id)
        if result is None:
            return None
        return QuotationInDb.model_validate(result)
