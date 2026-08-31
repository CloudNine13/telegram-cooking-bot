# Telegram Cooking and Recipe Management Bot

## Overview

The Telegram Cooking and Recipe Management Bot is an asynchronous Telegram service engineered for structured recipe cataloging, inventory-based recipe matching, and multi-format media ingestion. The platform enables regular users to explore hierarchical dish categories, match available fridge ingredients against recipe requirements, bookmark favorites, and access cooking guides in diverse media formats. Authorized administrators are provided with finite-state machine (FSM) workflows for catalog curation, recipe authoring, and background media processing.

---

## Key Features

### 1. Hierarchical Catalog and Discovery
- **Two-Level Taxonomy**: Primary categories (Breakfast, First Courses / Soups, Salads, Appetizers, Desserts, Beverages) and subcategorized Main Dishes (Meat, Fish, Vegetables).
- **Dynamic Sorting**: Toggle list ordering between Alphabetical (A-Z) and Date Added (Newest first).
- **Inline Pagination**: Interactive pagination for navigating large recipe sets.
- **Scoped In-Category Search**: Real-time recipe search constrained to the active category or subcategory.

### 2. Fridge Inventory and Matching Engine
- **Inventory Tracking**: Manage personal fridge ingredients via comma-separated text entries, with support for viewing, appending, replacing, or clearing items.
- **Smart Matching Logic**:
  - **Ready to Cook (100% Match)**: Identifies recipes where all required ingredients are present in the user's inventory.
  - **Almost Ready (Partial Match)**: Identifies recipes with exactly 1 or 2 missing ingredients, explicitly highlighting absent items in the recipe view.
- **Ad-Hoc Ingredient Search**: Instant search querying recipes containing specified ingredients without modifying saved fridge state.

### 3. Rich Hybrid Content Cards
- **Structured Dish Cards**: Display preparation time, categorized ingredients with units, and step-by-step cooking instructions.
- **Multi-Format Media**:
  - Photos of prepared dishes.
  - Direct video uploads and cached Instagram Reels.
  - Attached PDF cooking guides and auto-generated web-to-PDF documents.
  - Direct links to original source web pages and Instagram publications.

### 4. User Profiles and Localization
- **Multilingual Support**: Fully localized interface supporting English (`en`) and Russian (`ru`).
- **Preferences Persistence**: User language preferences and favorites persisted in PostgreSQL.
- **Favorites Management**: One-click bookmarking with a dedicated paginated favorites view.

### 5. Administrative Management
- **Role-Based Access Control**: Administrative commands and handlers protected by user ID verification against configuration lists.
- **Interactive Recipe Creation**: Step-by-step FSM wizard supporting title, category assignment, preparation time, ingredient parsing, instructions, and media uploads.
- **Catalog Management**: Category and subcategory creation, modification, reordering, and recipe catalog curation.

---

## Architecture and Technology Stack

The application adheres to a clean layered architecture with strict separation between bot presentation, business logic, and data persistence layers.

### Technology Components
- **Language & Runtime**: Python 3.12+
- **Bot Framework**: `aiogram` 3.x (Dispatcher, Routers, Middlewares, Filters, FSM)
- **Database**: PostgreSQL 16
- **Database Toolkit & ORM**: SQLAlchemy 2.0 (Async mode with `asyncpg`)
- **Database Migrations**: Alembic
- **State Storage & Caching**: Redis 7 with `RedisStorage` (fallback to `MemoryStorage`)
- **Configuration & Validation**: Pydantic v2 and `pydantic-settings`
- **Package Management**: `uv`
- **Code Quality**: `ruff` (linter and formatter)
- **Containerization**: Docker Compose (PostgreSQL and Redis services)

---

## Directory Structure

```
telegram-cooking-bot/
├── app/
│   ├── bot/
│   │   ├── filters/          # Custom aiogram filters (e.g., AdminFilter)
│   │   ├── handlers/         # Domain-specific routers (catalog, fridge, search, favorites, admin)
│   │   ├── keyboards/        # Inline keyboard builders and CallbackData factories
│   │   ├── middlewares/      # Database session, authentication, services, and i18n middlewares
│   │   └── states/           # FSM state groups for wizards and inputs
│   ├── core/
│   │   ├── config.py         # Application settings loaded via pydantic-settings
│   │   ├── i18n/             # Localization catalogs, translator, and formatters
│   │   └── seeder.py         # Initial category and taxonomy seeder
│   ├── database/
│   │   ├── migrations/       # Alembic environment and version migration scripts
│   │   ├── models/           # SQLAlchemy 2.0 declarative database models
│   │   ├── repositories/     # Asynchronous database CRUD repositories
│   │   └── session.py        # Async engine configuration and session factory
│   ├── schemas/              # Pydantic data transfer objects and validation schemas
│   ├── services/             # Pure business logic and domain service implementations
│   └── main.py               # Bot entrypoint, middleware registration, and lifespan handlers
├── docker-compose.yml        # PostgreSQL and Redis container orchestration
├── pyproject.toml            # Project dependencies and tool configurations
├── alembic.ini               # Database migration configuration
└── README.md                 # Project documentation
```

---

## Configuration

Application configuration is managed via environment variables or a local `.env` file in the project root directory.

### Environment Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | String | `""` | Telegram Bot API token from BotFather. |
| `ADMIN_USER_IDS` | List / String | `[]` | Comma-separated or JSON list of Telegram user IDs with administrative privileges. |
| `DATABASE_URL` | String | `""` | Async connection string for PostgreSQL database. |
| `REDIS_URL` | String | `redis://localhost:6379/0` | Connection string for Redis instance. |
| `DEFAULT_LOCALE` | String | `"en"` | Default interface language fallback (`en` or `ru`). |

---

## Installation and Setup

### Prerequisites
- Python 3.12 or higher
- `uv` package manager
- Docker and Docker Compose (for database and cache infrastructure)

### 1. Clone the Repository
```bash
git clone <repository_url>
cd telegram-cooking-bot
```

### 2. Configure Environment
Create a `.env` file in the project root:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ADMIN_USER_IDS=123456789,987654321
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=cooking_bot
POSTGRES_PORT=5432
REDIS_PORT=6379
DATABASE_URL=postgresql+asyncpg://postgres:your_secure_password@localhost:5432/cooking_bot
REDIS_URL=redis://localhost:6379/0
DEFAULT_LOCALE=en
```

### 3. Install Dependencies
Synchronize project dependencies using `uv`:
```bash
uv sync
```

### 4. Start Infrastructure Services
Launch PostgreSQL and Redis containers:
```bash
docker compose up -d
```

### 5. Apply Database Migrations
Run Alembic migrations to construct the database schema:
```bash
uv run alembic upgrade head
```

### 6. Run the Application
Execute the bot process:
```bash
uv run python -m app.main
```

---

## Database Management

Database schema versions are controlled via Alembic.

- **Apply all pending migrations**:
  ```bash
  uv run alembic upgrade head
  ```
- **Generate a new migration script**:
  ```bash
  uv run alembic revision --autogenerate -m "description_of_changes"
  ```
- **Downgrade database by one migration**:
  ```bash
  uv run alembic downgrade -1
  ```

---

## Code Quality Standards

The project enforces strict type hints and consistent formatting across all modules.

- **Lint Codebase**:
  ```bash
  uv run ruff check .
  ```
- **Fix Lint Issues**:
  ```bash
  uv run ruff check . --fix
  ```
- **Format Codebase**:
  ```bash
  uv run ruff format .
  ```
