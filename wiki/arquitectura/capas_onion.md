---
type: doc
title: Arquitectura — Capas Onion y Desacoplamiento de Dominio
description: Estructura concéntrica de capas, responsabilidades y desacoplamiento estricto de excepciones HTTP.
tags: [architecture, onion, layers, clean_code, exceptions]
timestamp: 2026-09-28T18:30:00Z
---

# 🧅 Capas Onion y Desacoplamiento de Dominio

La aplicación sigue el principio de dependencias concéntricas: las capas externas conocen a las internas, pero las internas nunca deben depender de las capas de transporte ni de librerías HTTP.

---

## 1. Responsabilidad por Capa

1. **Router (`app/api/v1/<entity>/<entity>_router.py`)**:
   - Define las rutas, parámetros de URL (`Path`, `Query`), códigos de estado de éxito y esquemas OpenAPI.
   - **Solo delega al Controller**. No contiene lógica de negocio ni persistencia.
2. **Controller (`app/api/v1/<entity>/<entity>_controller.py`)**:
   - Orquesta la llamada a Repositorios o a managers de la capa `serum.core`.
   - Empaqueta las respuestas en wrappers estandarizados (ej. `ListResponse`).
3. **Repository (`packages/serum-business/src/serum/repos/v1/<entity>/<entity>_repository.py`)**:
   - Importable como `serum.repos.v1.<entity>.<Entity>Repository`.
   - Encapsula las reglas de negocio de la entidad.
   - Genera UUIDs (`UuidTool.generate_uuid()`), timestamps (`TimeTools.get_now_in_milliseconds()`) y aplica el borrado lógico (`isDeleted = True`).
   - Solo interactúa con el `DataSource`.
4. **Core (`packages/serum-business/src/serum/core/`)**:
   - Importable como `serum.core.<module>`.
   - Módulos transversales y operaciones transaccionales complejas que involucran múltiples repositorios (ej. `OrderPaymentManager`, `CashRegisterManager`, `CashMovementManager`).
   - Gestión de seguridad, hashing de contraseñas y emisión de JWTs.
5. **DataSource (`packages/serum-business/src/serum/repos/v1/<entity>/data/<entity>_datasource.py`)**:
   - Interfaz de persistencia encargada de realizar queries a bajo nivel a la colección de base de datos.
6. **Collection (`packages/serum-business/src/serum/services/mongo_collections/v1/<entity>_collection.py`)**:
   - Importable como `serum.services.mongo_collections.v1.<Entity>Collection`.
   - Conecta con el driver asíncrono `AsyncMongoClient` de `pymongo`, extiende de `BaseMongoCollection` y provee acceso tipado a la colección física de MongoDB con soporte multi-tenant dinámico.

---

## 2. Tratamiento de Excepciones

- **Regla Estricta**: Las capas de Dominio (`Repository`) y de Orquestación (`Core`) **jamás deben importar ni lanzar `HTTPException`**.
- Cuando ocurre un error de negocio (ej. caja ya abierta, saldo insuficiente, orden no encontrada), se lanza una excepción de dominio (ej. `CashRegisterAlreadyOpen`, `InsufficientMethodBalance`).
- Todas las excepciones de dominio se centralizan en `app/regis_exception_handlers.py`, donde se registran como manejadores de FastAPI para transformar el error de negocio en el código HTTP correspondiente (400, 403, 404, 409, etc.) con una respuesta JSON limpia.
