# fastapi-onion-template

## 📄 Description

This is a project template based on **Onion Architecture**, designed to build robust and scalable APIs with **FastAPI**. It comes bundled with a custom **CLI (Command Line Interface)** (`onion-cli`) that automates the generation of new entities and their corresponding layers (Models, Repositories, Controllers, Routers), facilitating fast and consistent development.

### Data Flow   
`Router` → `Controller` → `Repository` → `DataSource` → `Service`.

This architecture was inspired by [Bloc Library's architecture](https://bloclibrary.dev/architecture/),

The primary goals of this template are:
* To promote clear and clean separation of concerns.
* To reduce complexity and coupling.
* To facilitate testability and code maintainability.
* To accelerate new feature development by automating layer creation.

## 🚀 Getting Started

### 1. Clone the Repository

### 2. Configure Environment and Install Dependencies with uv
```bash
pip install uv
uv sync
```

## ⚙️ Using the CLI (`onion`)
The core of this template is the custom `onion` CLI that automates the generation of your modules and other project components.

### Basic Syntax
After activating your virtual environment, you can run CLI commands using:
```bash
onion [command] [arguments] [options]
```
> write your entities in **singular**, for example: `onion crud product --version 1`  
> If your entities has two words, split them with underscore, for example: `onion crud product_category --version 1`

For a comprehensive list of commands and their detailed help, execute:

```bash
onion --help
```

### Available Commands
The onion CLI provides the following commands for generating project components. Each command typically accepts an <entity-name> argument.

- `crud <entity-name>`  
Creates the router, controller, and module files for a new entity. This is the most common command for full entity generation.

- `crud-mongo <entity-name>`  
Creates the router, controller, module files, and automatically handles the MongoDB collection setup for a new entity. Use this if your project uses MongoDB.

- `repo <entity-name>`  
Creates only the module (model, repository) files for an entity, without generating the API router.

- `repo-mongo <entity-name>`  
Creates only the module files for an entity and handles the MongoDB collection setup.

- `router <entity-name>`  
Creates only the API router file for an entity.

### example 
```bash
# Generate a full CRUD entity for 'Product' (router, controller, repository)
onion crud product --version 1

# Generate a full CRUD entity for 'Order' with MongoDB collection setup
onion crud-mongo order --version 2

# Generate only the repo files for 'ShoppingCart'
onion repo shopping_cart --version 1
```
> `--version` is required

### Important Note on API Versioning
When a new API version (e.g., `v2`, `v3`) is created, its main router (e.g., `app/api/v2/router.py`) must be manually included in the `app/main.py` file. The CLI does not automate this step to provide explicit control over API routing. You will need to add a line like `app.include_router(router_vX, prefix="/api/vX")` for each new version.
## 📁 Project Structure
This project's structure is designed following the principles of Onion Architecture, promoting a clear separation of concerns, low coupling, and high testability. Below is a detailed explanation of each top-level directory within the app/ folder:

- `api/`  
Declares API routes and controllers, often versioned (e.g., api/v1/). It orchestrates incoming requests and routes them to the application logic.

- `config/`  
Contains configuration files, it could include environment variables and settings. `Onion CLI` creates a `onion-config.toml` file in this folder when is required.


- `core/`  
Contains crucial, shared functionalities beyond simple CRUD, such as notifications, emails, or payment processing. These are core business actions interacting across the system.

- `repos/`  
Holds entity-specific logic, with a dedicated folder per entity (e.g., repos/v1/user/). Each repository encapsulates an entity's CRUD operations.

- `responses/`  
Contains Pydantic models for API responses, which may differ from internal data models. These models can also be versioned.

- `services/`  
Dedicated to accessing external services like databases (e.g., MongoService), Redis, or third-party APIs (e.g., PaypalService). This outermost layer handles external interactions.

- `tools/`  
Contains general-purpose utilities and support tools that are not core business features, such as date helpers, format converters, or other auxiliary classes.

### Important Root Files in app/ (additional):

- `.env.example`  
An example file for environment variables, guiding users on necessary configurations.
app_lifespan.py: Contains logic for FastAPI application's startup and shutdown events, such as establishing or closing database connections.

- `conftest.py`  
Configuration file for Pytest, used to define fixtures and hooks for testing.

- `main.py`  
The main entry point for the FastAPI application.
## 🤝 Contributions
Contributions are welcome! If you have ideas to improve this template or the CLI, feel free to open an issue or submit a pull request.