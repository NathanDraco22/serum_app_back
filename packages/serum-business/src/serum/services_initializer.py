from serum.services.mongo_service import MongoService


async def init_business_services() -> None:
    """
    Inicialización en el arranque del servidor (lifespan).
    Solo establece el pool de conexiones de MongoDB con AsyncMongoClient.
    NO crea índices ni colecciones fijas, ya que cada tenant se aprovisiona
    bajo demanda al activarse.
    """
    await MongoService().init_client()


async def init_services(nickname: str = "SerumDB") -> None:
    """
    Utilidad para tests unitarios y suites de integración.
    Conecta el cliente y aprovisiona una base de datos completa para pruebas.
    """
    await MongoService().init_client()
    from serum.core.tenant import provision_tenant

    await provision_tenant(nickname=nickname)

