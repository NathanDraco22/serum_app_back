# Serum Business

Paquete de lógica de negocio, modelos de persistencia, servicios y acceso a datos para el servidor Serum LIS.

Estructura modular:
- `serum.serum_config`: Configuración operativa y contexto multi-tenant (`serumCtx`, `SerumContext`).
- `serum.core`: Orquestadores transaccionales, gestores de dominio, seguridad y excepciones.
- `serum.repos`: Modelos Pydantic, repositorios y data sources.
- `serum.services`: Infraestructura de base de datos (`MongoService`, colecciones e índices).
- `serum.tools`: Utilidades de tiempo, búsqueda, UUIDs y configuración.
