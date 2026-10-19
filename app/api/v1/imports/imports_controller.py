from serum.core.default_values import ImportCatalogResult, create_default_lab_tests


class ImportsController:
    async def import_default_catalog(self) -> ImportCatalogResult:
        """Activa o re-ejecuta la importación del catálogo por defecto para el tenant actual."""
        result = await create_default_lab_tests()
        return result


imports_controller = ImportsController()
