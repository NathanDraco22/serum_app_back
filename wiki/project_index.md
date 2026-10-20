---
type: index
title: Backend — Mapa del Proyecto (Project Index)
description: Mapa maestro y exhaustivo de la arquitectura, módulos, endpoints, capas Onion y modelos del servidor FastAPI.
tags: [backend, architecture, fastapi, index, map, onion]
timestamp: 2026-09-28T18:30:00Z
---

# 🗺️ Project Index — Backend (Serum App LIS)

Este documento es el **mapa central y rector** del backend. Cualquier agente o desarrollador que trabaje en `serum_app_back` debe utilizar este índice para ubicarse en la arquitectura, ubicar los archivos correspondientes a cada dominio y respetar las reglas de negocio establecidas.

---

## 🏛️ 1. Arquitectura Onion y Estructura de Capas

El backend está construido con **FastAPI** y **MongoDB (asynchronous via `pymongo`)**, implementando estrictamente la **Arquitectura Onion**:

```
[ Capa de Transporte & API (FastAPI Routers, Controllers) ]
                      ↓
[ Capa de Dominio & Orquestación (Repositories, Core Services) ]
                      ↓
[ Capa de Infraestructura & Persistencia (DataSources, MongoDB Collections) ]
```

### Flujo de una Petición:
```
Cliente HTTP 
   ➔ Router (`app/api/v1/<entity>/<entity>_router.py`)
   ➔ Controller (`app/api/v1/<entity>/<entity>_controller.py`)
   ➔ Repository (`packages/serum-business/src/serum/repos/v1/<entity>/<entity>_repository.py`)
      (o Core Manager en `serum.core.<module>` para operaciones transaccionales complejas)
   ➔ DataSource (`serum.repos.v1.<entity>.<entity>_data_source.py`)
   ➔ Collection (`serum.services.mongo_collections.v1.<entity>_collection.py`)
   ➔ MongoDB (con resolución de base de datos dinámica por tenant según `serumCtx.get().businessNickname`)
```

---

## 📦 2. Árbol General de Directorios del Servidor

```
serum_app_back/
├── app/                                # Capa de Transporte, API HTTP y Middlewares
│   ├── main.py                         # Inicialización de FastAPI, CORS y registro de routers
│   ├── app_lifespan.py                 # Ciclo de vida (startup/shutdown) e inicio de servicios de negocio
│   ├── regis_exception_handlers.py     # Manejador centralizado: DomainException → HTTP Status
│   ├── api/v1/                         # Routers y Controllers HTTP por entidad
│   ├── app_middleware/                 # Middlewares (auth_middleware, api_key_middleware, multi_tenant_middleware)
│   ├── responses/                      # Wrappers de respuesta HTTP (ej. ListResponse)
│   └── config/                         # Configuraciones del servidor (onion-config.toml, pem)
├── packages/
│   └── serum-business/                 # Paquete independiente de Dominio y Persistencia (instalado editable)
│       ├── pyproject.toml              # Definición del paquete Python de negocio
│       └── src/serum/
│           ├── serum_config.py         # Configuración y contexto multi-tenant (SerumConfig, SerumContext, serumCtx)
│           ├── services_initializer.py # Inicialización de base de datos e índices
│           ├── core/                   # Orquestadores transaccionales, managers, seguridad y excepciones
│           ├── repos/v1/               # Modelos Pydantic, Repositorios y DataSources
│           ├── services/               # Conexión a MongoDB (MongoService multi-tenant, colecciones e índices)
│           └── tools/                  # Utilidades transversales (UUID, Time, Search, AppSettings)
├── test/                               # Suite de pruebas unitarias y de integración
├── wiki/                               # Wiki dedicada del servidor
│   ├── project_index.md                # ESTE ARCHIVO (Mapa rector del proyecto)
│   ├── AGENTS.md                       # Protocolo obligatorio para agentes IA
│   ├── INDEX.md                        # Índice de navegación OKF
│   ├── reglas_negocio/                 # Especificación de reglas médicas, caja y cotizaciones
│   └── arquitectura/                   # Detalle de capas y convenciones de código
├── AGENTS.md                           # Guía de estilo y convenciones del backend
└── pyproject.toml                      # Gestión de dependencias raíz (uv / Python)
```

---

## 🧭 3. Módulos y Entidades del Sistema

| Módulo / Entidad | Router & Controller (`app/api/v1/`) | Repositorio & DataSource (`serum.repos.v1`) | Colección MongoDB (`serum.services.mongo_collections.v1`) | Reglas de Negocio Clave |
| :--- | :--- | :--- | :--- | :--- |
| **Auths** | `auths/` | Autenticación, JWT, hashing | `users_collection.py` | JWT HS256, session (8h), refresh (30d), `/check-user`. Ver [Autenticación y Roles](reglas_negocio/autenticacion_y_roles.md). |
| **Branches** | `branches/` | `branches/` | `branches_collection.py` | Sedes físicas del laboratorio que segmentan cajas, usuarios y flujo de dinero. |
| **Roles** | `roles/` | `roles/` | `roles_collection.py` | Catálogo de roles con niveles jerárquicos (1 al 5). Admin=5, Operador=3. |
| **Users** | `users/` | `users/` | `users_collection.py` | Control de personal con `role` y `accessLevel: int` vinculados a sucursales. |
| **Patients** | `patients/` | `patients/` | `patients_collection.py` | Expediente demográfico maestro. Requiere `originBranch: str` para trazabilidad de creación. Requisito obligatorio para generar orden médica. |
| **Doctors** | `doctors/` | `doctors/` | `doctors_collection.py` | Catálogo de médicos referentes. Requiere `originBranch: str` para saber sucursal de alta. |
| **LabTests** | `lab_tests/` | `lab_tests/` | `lab_tests_collection.py` | Catálogo unificado global: Pruebas individuales y Packs (`isPack: true/false`). Ver [Catálogo LabTest](reglas_negocio/catalogo_lab_tests.md). |
| **LabTestAccounts** | `lab_test_accounts/` | `lab_test_accounts/` | `lab_test_accounts_collection.py` | Cuentas comerciales por sucursal (`branchId`, `labTestId`, `commercial: {salePrice, salePrice2, costPrice}`). Ver [Catálogo LabTest](reglas_negocio/catalogo_lab_tests.md). |
| **Quotations** | `quotations/` | `quotations/` | `quotations_collection.py` | Preventa y presupuestos con snapshots opcionales de cliente y médico (`clientInfo`, `doctorInfo`). Requiere `branchId: str`. Ver [Cotizaciones](reglas_negocio/cotizaciones.md). |
| **Orders** | `orders/` | `orders/` | `orders_collection.py` | **Snapshot Inmutable y Servicios**: Requiere `branchId: str`. Datos congelados de paciente, precios y parámetros. Soporte para servicios adicionales libres (`services: list[OrderService]`, ej. servicio a domicilio). Bloqueo de órdenes por precio modificado (`isBlocked`), auditoría de precio base con `originalPrice`, y endpoint `POST /orders/{id}/approve` para autorización por supervisores (`accessLevel > 3`). Ver [Snapshot y Órdenes](reglas_negocio/snapshot_y_ordenes.md). |
| **CashRegisters** | `cash_registers/` | `cash_registers/` | `cash_registers_collection.py` | Cajas físicas por sucursal (`branchId: str`), saldos por método (`cash`, `card`, `transfer`). |
| **CashShifts** | `cash_shifts/` | `cash_shifts/` | `cash_shifts_collection.py` | **Turnos de Caja ("La persona es la caja")**: Apertura con fondo inicial, corte y arqueo de caja con diferencias. |
| **CashMovements** | `cash_movements/` | `cash_movements/` | `cash_movements_collection.py` | **Movimientos Libres de Caja**: Ingresos y egresos libres vinculados a `shiftId` que actualizan saldo del turno e impactan Kardex. |
| **Receipts** | `receipts/` | `receipts/` | `receipts_collection.py` | **Recibos de Cobro**: Correlativo secuencial atómico (`next_receipt_number`), vinculados a órdenes médicas y turnos de caja. |
| **CashTransactions** | `cash_transactions/` | `cash_transactions/` | `cash_transactions_collection.py` | **Kardex Inmutable**: Libro contable de auditoría (`branchId: str`, `registerId: str`, `shiftId: str`); solo lectura (GET ALL). Ver [Caja y Kardex](reglas_negocio/caja_y_kardex.md). |
| **CoreSettings** | `core_settings/` | `core_settings/` | `core_settings_collection.py` | **Activación y Licencia de Servin**: Push con Ed25519 (EdDSA), auto-aprovisionamiento de branch/Admin y `/auths/servin-status`. |
| **Counters** | N/A (Interno) | `counters/` | `counters_collection.py` | **Correlativos e IDs Secuenciales**: Colección atómica con `$inc` y `upsert` para IDs de pacientes, doctores, órdenes, cotizaciones y turnos de caja. |
| **Reports** | `reports/` | N/A (Agregaciones) | Varias colecciones | **Business Intelligence**: 5 pipelines de agregación nativos en MongoDB (Financiero, Top Médicos, Demanda de Exámenes, Cuentas por Cobrar y Auditoría de Arqueos). Ver [Reportes Analíticos](reglas_negocio/reportes_analiticos.md). |
| **ApiKeys** | `api_keys/` | `api_keys/` | `api_keys_collection.py` | **Integraciones y Acceso Externo**: Llaves prefijadas `srm_live_...`, enmascaramiento, scopes (`bi:read`), soft delete y validación unificada en `app_middleware`. |
| **AppSettings** | `app_settings/` | `app_settings/` | `app_settings_collection.py` | **Configuración Global del Sistema**: Parámetros operativos y comerciales (`useCost`, `usePrice2`, `allowEditPrice`). Valores por defecto en `False`, inicialización en lifespan y caché en memoria con `AppSettingsTool`. Ver [Configuración del Sistema](reglas_negocio/configuracion_sistema.md). |
| **Imports** | `imports/` | N/A (`serum.core.default_values`) | `lab_tests_collection.py`, `lab_test_accounts_collection.py` | **Importaciones del Sistema**: `POST /imports/default-catalog` y alias `/imports/lab-tests` para inicializar o re-ejecutar la carga del catálogo maestro de pruebas clínicas (`lab_tests_master.json`) en el tenant activo, con seguridad híbrida (Super Token o JWT Admin con `accessLevel >= 4`) y respuesta estructurada `ImportCatalogResult`. |



---

## ⚙️ 4. Capa Core y Orquestaciones Transaccionales (`serum.core`)

Ubicada en `packages/serum-business/src/serum/core/`, maneja operaciones críticas que cruzan múltiples entidades y requieren consistencia atómica:

1. **`serum.core.cash_register`**:
   - `CashRegisterManager`: Orquestador de operaciones de caja.
   - `process_opening.py`: Apertura de caja (crea transacción `opening` tipo `in` y marca `isOpen = True`).
   - `process_closing.py`: Cierre y arqueo de caja (transacción `closing` tipo `out` y marca `isOpen = False`).
   - `process_income.py`: Ingresos extraordinarios de dinero (tipo `in`).
   - `process_withdrawal.py`: Retiros o egresos de caja (tipo `out`).
   - `process_payment.py`: Procesamiento de pagos directos a la caja.

2. **`serum.core.cash_movements`**:
   - `CashMovementManager`: Orquestador de movimientos libres de caja.
   - `process_cash_movement.py`: Transacción MongoDB atómica para procesar ingresos y egresos libres: valida turno abierto y fondos disponibles en retiros, actualiza atómicamente el balance del turno (`CashShift`), inserta el movimiento (`CashMovement`) y genera el asiento contable inmutable en el Kardex (`CashTransaction`).

3. **`serum.core.order_payment`**:
   - `OrderPaymentManager`: Orquesta el cobro de una orden médica y su reflejo inmediato en el balance de la caja activa y en el Kardex.
   - Valida el bloqueo de orden: Si `order.isBlocked == True`, aborta la transacción y lanza `OrderIsBlocked` (HTTP 400).
   - Actualiza el estado de la orden (`pending` ➔ `partiallyPaid` ➔ `paid`) y genera el recibo automático (`Receipt`).

4. **`serum.core.reports`**:
   - `ReportsManager`: Fachada orquestadora analítica.
   - `reports_pipelines.py`: Pipelines de agregación de MongoDB ($match, $group, $sort).
   - `generators/`: Módulos delegados (`generate_financial_report.py`, `generate_top_doctors_report.py`, `generate_lab_tests_volume_report.py`, `generate_pending_balances_report.py`, `generate_shifts_audit_report.py`, `reports_helpers.py`).

5. **`serum.core.counter_manager`**:
   - `CounterManager`: Orquestador transversal Singleton de correlativos e identificadores secuenciales.
   - Genera IDs formateados: `patientNumber` y `doctorNumber` (4 dígitos `zfill(4)`), `orderNumber`, `quotationNumber` y `shiftNumber` (numérico simple `str`).
   - Utiliza `$inc` atómico y `find_one_and_update(..., upsert=True)` en MongoDB.

6. **`serum.core.lab_tests`**:
   - `LabTestsManager`: Orquestador de creación atómica de pruebas clínicas y aprovisionamiento de cuentas por sucursal.
   - `process_create_lab_test.py`: Transacción en MongoDB para insertar `LabTest` + `LabTestAccount` de origen + cuentas en 0 para las demás sucursales.

7. **`serum.core.security`**:
   - `token_manager.py`: Creación y validación de tokens JWT (HS256) con expiraciones en segundos Unix.
   - `password_hasher.py`: Hashing y verificación de contraseñas mediante `passlib` / `bcrypt`.

8. **`serum.core.exceptions`**:
   - Excepciones de dominio desacopladas de FastAPI (ej. `CashRegisterAlreadyOpen`, `OrderNotFound`, `InsufficientMethodBalance`).
   - Se registran en `app/regis_exception_handlers.py` para retornar el código HTTP apropiado.

9. **`serum.core.default_values`**:
   - Inicialización idempotente en startup (`lifespan` ➔ `serum.services_initializer.init_business_services`):
     - `create_default_branch.py`: Creación de sucursal inicial `ORIGIN_BRANCH` ("Origen").
     - `create_default_cash_register.py`: Creación de caja registradora inicial `ORIGIN_CASH` ("Caja Principal") asociada a `ORIGIN_BRANCH`.
     - `create_root_user.py`: Creación de usuario administrador `Serum` (clave `SerumRoot`).


---

## 💎 5. Convenciones Críticas de Persistencia y Datos

1. **Valores Monetarios en Centavos (`int`)**:
   - Todos los precios, montos cobrados y balances (`totalAmount`, `salePriceApplied`, `cashBalance`, `amount`, etc.) se almacenan como enteros en centavos. Nunca se usa `float`.
2. **Timestamps en Milisegundos Unix (`int`)**:
   - `createdAt` y `updatedAt` de las entidades en base de datos se registran en milisegundos (`TimeTools.get_now_in_milliseconds()`).
   - Los claims de JWT (`exp`, `iat`) utilizan segundos Unix según el estándar RFC 7519.
3. **Pydantic Modelos en `camelCase`**:
   - Los campos de Pydantic usan `camelCase` (`patientId`, `isDeleted`, `salePrice`) para coincidir 1:1 con MongoDB y el cliente Flutter.
4. **Soft Delete**:
   - Todas las colecciones implementan borrado lógico mediante `isDeleted: bool = False`. La eliminación física en MongoDB está prohibida.
5. **Driver de MongoDB**:
   - Uso exclusivo de la API asíncrona de `pymongo` (`AsyncMongoClient`, `AsyncCollection`).

---

## 🏛️ 6. Paquete de Negocio (`serum-business`) y Contexto Multi-Tenant

Para la especificación técnica profunda de la separación del paquete de negocio y la arquitectura multi-tenant, consulta:  
- 👉 **[Arquitectura Multi-Tenant y Aprovisionamiento (multi_tenant.md)](arquitectura/multi_tenant.md)**: Guía completa del modelo *Database-per-Tenant*, aprovisionamiento atómico, middleware `ContextVar` y conexión con Flutter.
- 👉 **[Paquete serum-business y Modularización (serum_business_package.md)](arquitectura/serum_business_package.md)**: Desacoplamiento de capas, árbol de código y namespaces de import.

### Resumen del Mecanismo Multi-Tenant:
1. **Modelo Database-per-Tenant**: Cada laboratorio tiene su base de datos física dedicada (`client.get_database(nickname)`), eliminando discriminadores lógicos y garantizando aislamiento estricto.
2. **Contexto Asíncrono**: `serum.serum_config.serumCtx` almacena `SerumContext(businessNickname, branchId)` por corrutina mediante `contextvars.ContextVar`.
3. **Middleware de Entrada**: `app/app_middleware/depends/multi_tenant.py` (`multi_tenant_middleware`) extrae los headers obligatorios `x-tenant-nickname` / `X-Servin` y `x-branch` / `x-branch-id`, asignando y limpiando el contexto con `try ... finally: serumCtx.reset(token)`.
4. **Instancias Aisladas de Colección**: `BaseMongoCollection._instances` mantiene un pool de instancias indexado por `nickname`.
5. **Resolución de Base de Datos**: `serum.services.mongo_service.MongoService.get_collection()` resuelve dinámicamente `ctx.businessNickname` (directamente el `nickname`) si `businessNickname` está presente, o recurre a la base de datos por defecto (`SerumDB` / `DB_NAME`).
6. **Aprovisionamiento Atómico**: `serum.core.tenant.provision_tenant.provision_tenant()` inicializa bajo demanda colecciones, índices, sucursal, roles, caja, settings, catálogo de pruebas y usuarios sin necesidad de reiniciar el servidor.
