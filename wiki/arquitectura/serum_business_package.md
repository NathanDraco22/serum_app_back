---
type: doc
title: Arquitectura — Paquete serum-business y Multi-Tenancy con ContextVar
description: Especificación completa de la extracción del paquete de negocio serum-business, estructura de namespaces y mecanismo de multi-tenancy con contextvars.
tags: [architecture, package, serum-business, multi-tenant, contextvars, pymongo]
timestamp: 2026-10-17T19:30:00Z
---

# 📦 Paquete `serum-business` y Arquitectura Multi-Tenant

Este documento describe la estructura modular del paquete independiente **`serum-business`** y la infraestructura preparada para el soporte **Multi-Tenant** mediante `contextvars.ContextVar`.

---

## 1. Motivación y Principio de Separación

Siguiendo el patrón arquitectónico probado en `kardex_app/kardex-server/packages/kardex-business`:
1. **Desacoplamiento Total de Transporte**: `serum_app_back/app/` solo contiene la capa de transporte HTTP (FastAPI, routers, controllers, middlewares y schemas de respuesta).
2. **Lógica de Negocio Pura**: `serum_app_back/packages/serum-business/` contiene toda la lógica de dominio, modelos Pydantic, orquestaciones transaccionales, repositorios, colecciones de MongoDB y utilidades.
3. **Instalación Editable**: Se instala como dependencia en `serum_app_back/pyproject.toml` usando `uv`:
   ```toml
   [tool.uv.sources]
   serum-business = { path = "./packages/serum-business", editable = true }
   ```
4. **Namespace Limpio**: Todo el código se importa desde el namespace raíz `serum.*` (ej. `from serum.repos.v1.patients import PatientsRepository`).

---

## 2. Árbol de Directorios del Paquete `serum-business`

```
packages/serum-business/
├── pyproject.toml                      # Metadatos del paquete y dependencias de persistencia
├── README.md
└── src/serum/
    ├── __init__.py                     # Package root
    ├── serum_config.py                 # SerumConfig, SerumContext, serumCtx (ContextVar)
    ├── services_initializer.py         # init_business_services() (Mongo + índices + defaults)
    ├── core/                           # Capa de orquestación transaccional y seguridad
    │   ├── cash_movements/             # CashMovementManager y transacciones de caja libre
    │   ├── cash_register/              # CashRegisterManager (apertura, cierre, retiros, ingresos)
    │   ├── counter_manager/            # CounterManager (correlativos atómicos con $inc)
    │   ├── default_values/             # Inicialización de sucursales, roles, usuario root, settings
    │   ├── exceptions/                 # Excepciones de dominio puras (sin dependencia HTTP)
    │   ├── lab_tests/                  # LabTestsManager (creación atómica con cuentas)
    │   ├── order_payment/              # OrderPaymentManager (cobros, recibos, validación de bloqueo)
    │   ├── reports/                    # ReportsManager y pipelines de agregación BI
    │   └── security/                   # TokenManager (JWT HS256) y SysPasswordHasher (Argon2)
    ├── repos/v1/                       # Modelos Pydantic, Repositorios y DataSources por entidad
    │   ├── api_keys/
    │   ├── app_settings/
    │   ├── branches/
    │   ├── cash_movements/
    │   ├── cash_registers/
    │   ├── cash_shifts/
    │   ├── cash_transactions/
    │   ├── common/                     # Modelos compartidos (filter_params, user_info, etc.)
    │   ├── core_settings/
    │   ├── counters/
    │   ├── doctors/
    │   ├── lab_test_accounts/
    │   ├── lab_tests/
    │   ├── orders/
    │   ├── patients/
    │   ├── quotations/
    │   ├── receipts/
    │   ├── roles/
    │   └── users/
    ├── services/                       # Persistencia e infraestructura MongoDB
    │   ├── base_mongo_collection.py    # Clase base con property _collection dinámica
    │   ├── mongo_service.py            # MongoService con resolución dinámica de base de datos
    │   └── mongo_collections/v1/       # 17 colecciones tipadas de MongoDB
    └── tools/                          # Utilidades de bajo nivel
        ├── app_settings_tool.py        # Caché en memoria de configuración
        ├── search_tools.py             # Búsqueda diacrítica y regex
        ├── time_tools.py               # Timestamps en milisegundos Unix
        └── uuid_tool.py                # Generador de UUIDs v4 estándar
```

---

## 3. Índice Rápido de Imports para Agentes y Desarrolladores

| Dominio / Funcionalidad | Namespace de Import | Ejemplo de Clase / Función |
| :--- | :--- | :--- |
| **Contexto Multi-Tenant** | `serum.serum_config` | `SerumConfig`, `SerumContext`, `serumCtx` |
| **Startup del Negocio** | `serum.services_initializer` | `init_business_services()` |
| **Caja Registradora** | `serum.core.cash_register` | `CashRegisterManager` |
| **Movimientos Libres** | `serum.core.cash_movements` | `CashMovementManager` |
| **Cobros de Órdenes** | `serum.core.order_payment` | `OrderPaymentManager`, `OrderPayIntent` |
| **Correlativos e IDs** | `serum.core.counter_manager` | `CounterManager` |
| **Pruebas y Cuentas** | `serum.core.lab_tests` | `LabTestsManager` |
| **Seguridad y Tokens** | `serum.core.security` | `TokenManager`, `SysPasswordHasher` |
| **Excepciones de Dominio** | `serum.core.exceptions` | `OrderIsBlocked`, `CashShiftAlreadyOpen`, etc. |
| **Reportes Analíticos** | `serum.core.reports` | `ReportsManager` |
| **Repositorios de Datos** | `serum.repos.v1.<entity>` | `PatientsRepository`, `OrdersRepository`, etc. |
| **Modelos Pydantic** | `serum.repos.v1.<entity>` | `PatientInDb`, `CreateOrder`, `UserInDb`, etc. |
| **Servicio de MongoDB** | `serum.services` | `MongoService`, `BaseMongoCollection` |
| **Colecciones MongoDB** | `serum.services.mongo_collections.v1` | `OrdersCollection`, `PatientsCollection`, etc. |
| **Herramientas de Soporte**| `serum.tools` | `TimeTools`, `UuidTool`, `SearchTools`, `AppSettingsTool` |

---

## 4. Arquitectura Multi-Tenant con `ContextVar`

### A. Definición del Contexto (`serum_config.py`)
```python
import contextvars
from dataclasses import dataclass

@dataclass
class SerumContext:
    businessNickname: str = ""
    branchId: str = ""

serumCtx = contextvars.ContextVar("serumCtx", default=SerumContext())
```

### B. Middleware / Dependencia de FastAPI (`app_middleware/depends/multi_tenant.py`)
Extrae los encabezados enviados por el cliente (`x-tenant-nickname` y `X-Servin` / `x-branch-id`), inyecta el `SerumContext` en la corrutina asíncrona actual y garantiza su limpieza:

```python
async def multi_tenant_middleware(req: Request):
    tenant_nickname = req.headers.get("x-tenant-nickname")
    branch_id = req.headers.get("X-Servin") or req.headers.get("x-branch-id")

    new_ctx = SerumContext(
        businessNickname=tenant_nickname or "",
        branchId=branch_id or "",
    )

    token = serumCtx.set(new_ctx)
    try:
        yield
    finally:
        serumCtx.reset(token)
```

### C. Resolución Dinámica de Base de Datos (`MongoService.get_collection`)
Cuando se ejecuta cualquier consulta desde cualquier colección, `BaseMongoCollection._collection` invoca `MongoService.get_collection(...)`, el cual lee `serumCtx`:

```python
def get_collection(
    self,
    collection_name: str,
    database_name: DatabaseName = "SerumDB",
) -> AsyncCollection[dict[str, Any]]:
    from serum.serum_config import serumCtx

    ctx = serumCtx.get()
    if database_name:
        current_db_name = database_name
    elif ctx.businessNickname:
        current_db_name = ctx.businessNickname
    else:
        current_db_name = os.getenv("DB_NAME", "SerumDB")

    db = self.client.get_database(current_db_name)
    return db.get_collection(collection_name)
```

### D. Ventajas del Enfoque:
1. **Transparencia Total**: Los repositorios y managers no necesitan recibir un parámetro `tenant_id` en cada método; operan de manera agnóstica.
2. **Seguridad contra Fugas**: El bloque `try ... finally: reset(token)` evita que corrutinas reutilizadas en el event loop hereden contextos de peticiones previas.
3. **Compatibilidad Retrospectiva**: Si `businessNickname` no se provee (como ocurre actualmente), el sistema continúa apuntando a `SerumDB` de forma 100% transparente.
