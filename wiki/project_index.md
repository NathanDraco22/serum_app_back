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
   ➔ Repository (`app/repos/v1/<entity>/<entity>_repository.py`)
      (o Core Manager en `app/core/<module>/` para operaciones transaccionales complejas)
   ➔ DataSource (`app/repos/v1/<entity>/<entity>_data_source.py`)
   ➔ Collection (`app/services/mongo_collections/v1/<entity>_collection.py`)
   ➔ MongoDB
```

---

## 📦 2. Árbol General de Directorios del Servidor

```
serum_app_back/
├── app/
│   ├── main.py                         # Inicialización de FastAPI, CORS y registro de routers
│   ├── app_lifespan.py                 # Ciclo de vida (startup/shutdown) e inicio de servicios
│   ├── regis_exception_handlers.py     # Manejador centralizado: DomainException → HTTP Status
│   ├── api/v1/                         # Routers y Controllers por entidad
│   ├── core/                           # Lógica transversal, operaciones transaccionales y seguridad
│   ├── repos/v1/                       # Modelos Pydantic, Repositorios y DataSources
│   ├── services/                       # Infraestructura y conexión a MongoDB
│   ├── tools/                          # Utilidades transversales (UUID, Time, Search)
│   ├── responses/                      # Wrappers de respuesta HTTP (ej. ListResponse)
│   └── config/                         # Configuraciones del servidor
├── wiki/                               # Wiki dedicada del servidor
│   ├── project_index.md                # ESTE ARCHIVO (Mapa rector del proyecto)
│   ├── AGENTS.md                       # Protocolo obligatorio para agentes IA
│   ├── INDEX.md                        # Índice de navegación OKF
│   ├── reglas_negocio/                 # Especificación de reglas médicas, caja y cotizaciones
│   └── arquitectura/                   # Detalle de capas y convenciones de código
├── AGENTS.md                           # Guía de estilo y convenciones del backend
└── pyproject.toml                      # Gestión de dependencias (uv / Python)
```

---

## 🧭 3. Módulos y Entidades del Sistema

| Módulo / Entidad | Router & Controller (`app/api/v1/`) | Repositorio & DataSource (`app/repos/v1/`) | Colección MongoDB (`app/services/mongo_collections/v1/`) | Reglas de Negocio Clave |
| :--- | :--- | :--- | :--- | :--- |
| **Auths** | `auths/` | Autenticación, JWT, hashing | `users_collection.py` | JWT HS256, session (8h), refresh (30d), `/check-user`. Ver [Autenticación y Roles](reglas_negocio/autenticacion_y_roles.md). |
| **Branches** | `branches/` | `branches/` | `branches_collection.py` | Sedes físicas del laboratorio que segmentan cajas, usuarios y flujo de dinero. |
| **Users** | `users/` | `users/` | `users_collection.py` | Control de personal con roles (`admin`, `cashier`, `bioanalyst`, etc.) asignados a sucursales. |
| **Patients** | `patients/` | `patients/` | `patients_collection.py` | Expediente demográfico maestro. Requiere `originBranch: str` para trazabilidad de creación. Requisito obligatorio para generar orden médica. |
| **Doctors** | `doctors/` | `doctors/` | `doctors_collection.py` | Catálogo de médicos referentes. Requiere `originBranch: str` para saber sucursal de alta. |
| **LabTests** | `lab_tests/` | `lab_tests/` | `lab_tests_collection.py` | Catálogo unificado global: Pruebas individuales y Packs (`isPack: true/false`). Ver [Catálogo LabTest](reglas_negocio/catalogo_lab_tests.md). |
| **Quotations** | `quotations/` | `quotations/` | `quotations_collection.py` | Preventa para clientes casuales (texto libre). Requiere `branchId: str`. Ver [Cotizaciones](reglas_negocio/cotizaciones.md). |
| **Orders** | `orders/` | `orders/` | `orders_collection.py` | **Snapshot Inmutable**: Requiere `branchId: str`. Datos congelados de paciente, precios y parámetros. Ver [Snapshot y Órdenes](reglas_negocio/snapshot_y_ordenes.md). |
| **CashRegisters** | `cash_registers/` | `cash_registers/` | `cash_registers_collection.py` | Cajas físicas por sucursal (`branchId: str`), saldos por método (`cash`, `card`, `transfer`). |
| **CashTransactions** | `cash_transactions/` | `cash_transactions/` | `cash_transactions_collection.py` | **Kardex Inmutable**: Libro contable de auditoría (`branchId: str`, `registerId: str`); solo lectura (GET ALL). Ver [Caja y Kardex](reglas_negocio/caja_y_kardex.md). |

---

## ⚙️ 4. Capa Core y Orquestaciones Transaccionales (`app/core/`)

Ubicada en `app/core/`, maneja operaciones críticas que cruzan múltiples entidades y requieren consistencia atómica:

1. **`app/core/cash_register/`**:
   - `CashRegisterManager`: Orquestador de operaciones de caja.
   - `process_opening.py`: Apertura de caja (crea transacción `opening` tipo `in` y marca `isOpen = True`).
   - `process_closing.py`: Cierre y arqueo de caja (transacción `closing` tipo `out` y marca `isOpen = False`).
   - `process_income.py`: Ingresos extraordinarios de dinero (tipo `in`).
   - `process_withdrawal.py`: Retiros o egresos de caja (tipo `out`).
   - `process_payment.py`: Procesamiento de pagos directos a la caja.

2. **`app/core/order_payment/`**:
   - `OrderPaymentManager`: Orquesta el cobro de una orden médica y su reflejo inmediato en el balance de la caja activa y en el Kardex.
   - Actualiza el estado de la orden (`pending` ➔ `partiallyPaid` ➔ `paid`).

3. **`app/core/security/`**:
   - `token_manager.py`: Creación y validación de tokens JWT (HS256) con expiraciones en segundos Unix.
   - `password_hasher.py`: Hashing y verificación de contraseñas mediante `passlib` / `bcrypt`.

4. **`app/core/exceptions/`**:
   - Excepciones de dominio desacopladas de FastAPI (ej. `CashRegisterAlreadyOpen`, `OrderNotFound`, `InsufficientMethodBalance`).
   - Se registran en `app/regis_exception_handlers.py` para retornar el código HTTP apropiado.

5. **`app/core/default_values/`**:
   - Inicialización idempotente en startup (`lifespan` ➔ `services_initializer.py`):
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
