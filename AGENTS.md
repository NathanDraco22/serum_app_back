# Onion Fullstack Architecture & Style Guide
**General Development Standard (FastAPI + Flutter)**

This document establishes the architecture guidelines, coding standards, conventions, and development workflow for all projects in the ecosystem implementing the **Onion Architecture** pattern on both the Backend (FastAPI / Python) and Frontend (Flutter / Dart).

Any developer or AI agent working on this codebase **must** strictly adhere to these guidelines to ensure consistency, scalability, and readability across systems.

---

## 🏗️ 1. Architecture Philosophy & Data Flow

The core pillar of our development is the strict separation of concerns into concentric layers (Onion Architecture). Dependencies must always flow from the outer layers toward the inner layers, never the reverse.

```
[ Outer Layer: Transport & API (Routers, Controllers, Views, DataSources) ]
       ↓
[ Intermediate Layer: Orchestration & Business (Repositories, Core Services) ]
       ↓
[ Inner Layer: Domain & Persistence (Models, DB Collections, Tools) ]
```

---

## 🔧 2. Core Tool: Onion CLI

The structured creation of new modules or CRUDs must be done using the `onion` CLI. Creating base structures manually is prohibited to prevent naming errors.

> [!IMPORTANT]
> **Naming Rule**: All entity names provided to the CLI must be in the **singular** form (e.g., `product`, `client`, `expense_category`). The tool will automatically derive PascalCase and snake_case singular/plural variations.

### Available Commands Catalog

#### 🐍 Backend Commands (Python / FastAPI)
*   `onion crud-mongo <entity> --version <v>`: Generates the full structure integrated with MongoDB: Router, Controller, Pydantic Model, Repository, DataSource, and Collection. (Most commonly used in backend).
*   `onion repo-mongo <entity> --version <v>`: Generates the persistence layer with MongoDB (Model, Repository, DataSource, and Collection), omitting the HTTP layer.
*   `onion crud <entity> --version <v>`: Generates the basic structure with memory/stub persistence (Router, Controller, Model, Repository, and DataSource).
*   `onion repo <entity> --version <v>`: Generates basic persistence without MongoDB or API endpoints.
*   `onion router <entity> --version <v>`: Generates only FastAPI routers and controllers (uses `Any` placeholders).

#### 🎯 Frontend Commands (Dart / Flutter)
*   `onion dart <entity>`: Generates the client data layer: Models, DataSource, and Repository. (Symmetric equivalent to backend `crud`).
*   `onion dart-cubit <entity>`: Generates BLoC state management classes (`Read` and `Write` Cubits) with their state hierarchies.
*   `onion flutter-module <entity>`: Creates a complete UI and logic feature module: `cubit/`, `dialog/`, `view/`, and `widgets/` folders with ready-to-use stubs.
*   `onion dart-model <entity>`: Generates only the 4 typed Dart models (`Base`, `Create`, `Update`, `InDb`).
*   `onion dart-view <entity>`: Generates a basic screen view (StatelessWidget).
*   `onion barrel <directory>`: Generates a barrel file (`export.dart`) in a given directory, re-exporting all `.dart` files inside.

---

## 🐍 3. Backend Standards (FastAPI / Python)

### 3.1 Backend Layer Flow
```
Router (HTTP) ➔ Controller (Orchestration) ➔ Repository (Domain) ➔ DataSource (BD Querying) ➔ Collection (MongoDB Client)
```

1.  **Router**: Defines path endpoints (`/products`), path validation, and query parameters. Delegates execution to the controller.
2.  **Controller**: Receives the injected request, orchestrates repository or core service calls, and returns serialized responses.
3.  **Repository**: Encapsulates domain and business rules. Validates data, calculates IDs/timestamps, and calls the DataSource.
4.  **DataSource**: Low-level infrastructure layer for raw database queries or external API calls.
5.  **Collection**: Physical interface for the database driver (MongoDB/Motor), extending `BaseMongoCollection`.

### 3.2 Naming & Data Conventions
*   **CamelCase for Pydantic**: Pydantic model properties **must use camelCase** (e.g., `productId`, `createdAt`) to maintain strict parity with MongoDB document fields and Flutter model schemas.
*   **Date Types**: Always stored as integers (`int`) representing Unix Timestamps in milliseconds.
*   **Entity Names**: Always singular (`product`, `supplier`).
*   **Variables & Files**: `snake_case` format (`create_entity_by_id`, `entities_repository.py`).
*   **Classes**: `PascalCase` format (`EntitiesRepository`).

### 3.3 Post-Generation Manual Adjustments (Backend)
After running `onion crud-mongo` or `onion repo-mongo`, implement signatures and returns in the **Repository**:

*   **During Creation (`create`)**:
    Instantiate the DB model (`EntityInDb`) injecting a unique ID (`UuidTool.generate_uuid()`) and creation time (`TimeTools.get_now_in_milliseconds()`).
    ```python
    async def create_entity(self, create_entity: CreateEntity) -> EntityInDb:
        new_entity = EntityInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_entity.model_dump(),
        )
        result = await self.entity_ds.create_entity(new_entity.model_dump())
        return EntityInDb.model_validate(result)
    ```
*   **During Update (`update`)**:
    Extract only modified fields using `exclude_unset=True` inside `model_dump()`, and inject the update timestamp (`updatedAt`) to prevent overwriting existing MongoDB document fields with nulls:
    ```python
    async def update_entity_by_id(self, entity_id: str, entity: UpdateEntity) -> EntityInDb | None:
        updated_data = entity.model_dump(exclude_unset=True)
        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()
        
        result = await self.entity_ds.update_entity_by_id(entity_id, updated_data)
        if result is None:
            return None
        return EntityInDb.model_validate(result)
    ```

### 3.4 Core Layer (Complex Operations & Transversal Modules)
The `core/` folder (located inside the business package, e.g., `packages/kardex-business/src/kardex/core/` or `app/core/`) houses all complex business orchestrations exceeding a basic CRUD, transversal domain sub-modules, schedulers, and operational managers.

*   **Atomic Transactions (Recommendation)**: For complex write operations mutating multiple documents or collections critically (e.g., creating an invoice that simultaneously reduces stock and updates a client ledger balance), utilizing MongoDB transactions is recommended to guarantee physical atomicity. Not all logic inside `core` requires transactions:
    ```python
    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            # Transactional operations passing session=session
    ```
*   **Errors and Rollback**: If a MongoDB transaction is used and a domain exception is raised (e.g., inheriting from `BusinessException` or `DomainException`), the transaction will abort (rollback) automatically in MongoDB.
*   **Transversal Core Modules (e.g., `security`)**: Domain sub-modules like the `security/` folder (holding `token_manager.py` for JWT operations and `password_hasher.py` for password hashing) must reside in `core/`, completely decoupled from the API and transport layer.
*   **Services Initializer (`services_initializer.py`)**: This startup script resides in the API core layer (`app/core/services_initializer.py` or equivalent) and orchestrates execution of all bootstrap tasks required when launching the FastAPI server (e.g., starting database connections, seeding defaults with `create_default_roles()`, and registering the admin account via `create_root_user()`).
*   **Non-CRUD Managers and Use Cases (e.g., `ImageUploader`, `ClipboardManager`)**: Pure operational processes interacting with output services that do not represent a database CRUD entity (and thus do not require a repository or datasource). These reside in `core/` and are invoked directly by the UI or controllers to interact with underlying technical services.
*   **Task Schedulers**: Automated, time-based background tasks or workers (such as daily cron jobs executed at midnight to generate executive reports or Telegram notifications) residing in `core/` (e.g., `core/scheduler/`) that autonomously orchestrate calls to business repositories or notification services.

### 3.5 FastAPI Decoupling & Exceptions
*   **Rule**: The business package (e.g., `kardex-business` or logic package) must not depend on FastAPI. **Never** raise `HTTPException` from the repository or core layer.
*   **Handling**: Raise domain exceptions inheriting from `BusinessException`. In the API layer, register these exceptions in the centralized exception handler (e.g., `regis_exception_handlers.py` or middleware) to map them to the corresponding HTTP codes (400, 403, 404, etc.).

---

## 🛠️ 4. Project-Specific Conventions (Serum App - LIS)

### 4.1 ListResponse Wrapper
All `GET ALL` endpoints **must** return `ListResponse[T]` instead of bare `list[T]`. This wraps the array in `{ count: int, data: list[T] }`.

Import from `responses.v1`:
```python
from responses.v1 import ListResponse
```

Use in Controller:
```python
async def get_all_entities(self) -> ListResponse[EntityInDb]:
    entities = await self.repo.get_all_entities()
    return ListResponse(count=len(entities), data=entities)
```

Use in Router:
```python
from responses.v1 import ListResponse

@router.get("")
async def get_all() -> ListResponse[EntityInDb]:
    return await controller.get_all()
```

### 4.2 Soft Delete Pattern
All entities support soft delete via `isDeleted: bool = False` in the `InDb` model. The delete operation updates the document to set `isDeleted = True` rather than removing it.

**DataSource/Collection (MongoDB):**
```python
async def delete_entity_by_id(self, entity_id: str) -> dict[str, Any] | None:
    result = await collection.find_one_and_update(
        {"id": entity_id},
        {"$set": {"isDeleted": True}},
        return_document=ReturnDocument.AFTER,
    )
    return result
```

**DataSource (in-memory fallback):**
```python
async def delete_entity_by_id(self, entity_id: str) -> dict[str, Any] | None:
    if entity_id not in self._entities:
        return None
    self._entities[entity_id]["isDeleted"] = True
    return self._entities[entity_id]
```

### 4.3 MongoDB Driver: pymongo only
Use `pymongo`'s **asynchronous** API exclusively. Do NOT use `motor`.

- `from pymongo import AsyncMongoClient`
- `from pymongo.asynchronous.collection import AsyncCollection`
- `from pymongo import ReturnDocument`

### 4.4 Services Layer
`MongoService` is a singleton (via `__new__`) that lazily connects to MongoDB. It must be initialized during app startup:

```python
# app/core/services_initializer.py
from services.mongo_service import MongoService

async def init_services() -> None:
    await MongoService().init_service()
```

`init_services()` is called from the FastAPI lifespan (`app_lifespan.py`).

### 4.5 BaseMongoCollection Import (Circular Import Fix)
When importing `MongoService` inside `base_mongo_collection.py`, use the **direct module path** to avoid circular imports with `services/__init__.py`:

```python
# ✅ Correct - direct import avoids circular dependency
from services.mongo_service import MongoService

# ❌ Wrong - creates circular import
from services import MongoService
```

### 4.6 Known CLI (`onion crud-mongo`) Issues & Fixes
After running `onion crud-mongo`, the following manual fixes are required:

1. **`mongo_service.py`** — CLI generates broken import `from pymongo.asynchronous import`. Fix:
   ```python
   from pymongo import AsyncMongoClient
   from pymongo.asynchronous.collection import AsyncCollection
   ```
2. **Model fields** — CLI generates empty `BaseModel` subclasses. Add fields manually.
3. **Repository `create`/`update`** — CLI leaves `NotImplementedError`. Implement following the pattern in Section 3.3.

### 4.7 Repository Imports Restriction
Repository layer **must only import from `tools`** for cross-cutting utilities (UUID, time). It must **not** import from `services`, `collections`, or any infrastructure layer directly.

```python
# ✅ Correct
from tools.time_tools import TimeTools
from tools.uuid_tool import UuidTool

# ❌ Wrong
from services.mongo_service import MongoService
```

The infrastructure dependency is injected via the `DataSource`, which is passed to the Repository constructor.

---

## 🔧 5. Tools Reference

### UuidTool (`app/tools/uuid_tool.py`)
```python
class UuidTool:
    @staticmethod
    def generate_uuid() -> str:
        return str(uuid.uuid4())
```

### TimeTools (`app/tools/time_tools.py`)
```python
class TimeTools:
    @staticmethod
    def get_now_in_milliseconds() -> int:
        return int(datetime.now().timestamp() * 1000)
```

---