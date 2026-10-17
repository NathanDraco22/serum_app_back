from serum.core.default_values import (
    create_default_app_settings,
    create_default_branch,
    create_default_cash_register,
    create_default_lab_tests,
    create_default_roles,
    create_root_user,
)
from serum.core.reports.database_indexes import ensure_reports_indexes
from serum.services.mongo_collections.v1.api_keys_collection import ApiKeysCollection
from serum.services.mongo_service import MongoService
from serum.tools.app_settings_tool import AppSettingsTool


async def init_business_services() -> None:
    await MongoService().init_service()
    await ensure_reports_indexes()
    await create_default_branch()
    await create_default_cash_register()
    await create_default_roles()
    await create_root_user()
    await create_default_lab_tests()
    await create_default_app_settings()
    await AppSettingsTool().refresh_current_app_settings()
    await ApiKeysCollection.get_instance().create_indexes()


# Alias for compatibility
init_services = init_business_services
