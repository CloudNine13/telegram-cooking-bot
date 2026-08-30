# Telegram Cooking Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the complete asynchronous Telegram Cooking & Recipe Management Bot in Python 3.12+ using aiogram 3.x, SQLAlchemy 2.0 (asyncpg), PostgreSQL, Redis, and Pydantic v2.

**Architecture:** Layered asynchronous architecture consisting of configuration/i18n (`app/core/`), database models and async repositories (`app/database/`), Pydantic DTOs (`app/schemas/`), pure domain services (`app/services/`), aiogram 3.x bot components (middlewares, filters, keyboards, FSM states, handlers under `app/bot/`), and application lifespan entrypoint (`app/main.py`).

**Tech Stack:** Python 3.12, aiogram 3.x, SQLAlchemy 2.0 (asyncpg), Redis (redis-py async), Pydantic v2, pydantic-settings, ruff.

## Global Constraints
- Python 3.12+ strict typing on all function arguments, return types, class attributes, and variables.
- Zero comments or docstrings inside proprietary application code files.
- Code indentation: 4 spaces. Trailing commas in multiline object literals/lists.
- Routers only: no direct Dispatcher handlers.
- Typed CallbackData factories for all inline buttons with `F.filter()` routing.
- Dependency injection via aiogram middlewares (`DbSessionMiddleware`, `AuthMiddleware`, `UserI18nMiddleware`).
- Graphify extraction and Ruff linting after each phase.

---

### Task 1: Core Configuration and Localization (i18n)

**Files:**
- Create: `app/core/config.py`
- Create: `app/core/i18n/locales.py`
- Create: `app/core/i18n/translator.py`

**Interfaces:**
- Produces: `Settings`, `get_settings()`, `t(key: str, locale: str, **kwargs: Any) -> str`

- [ ] **Step 1: Create `app/core/config.py`**
Define `Settings` using `pydantic_settings.BaseSettings` loading `TELEGRAM_BOT_TOKEN`, `ADMIN_USER_IDS`, `DATABASE_URL`, `REDIS_URL`, `DEFAULT_LOCALE`.

- [ ] **Step 2: Create `app/core/i18n/locales.py`**
Define structured localization string dictionaries for English (`en`) and Russian (`ru`) covering all bot messages, menus, buttons, errors, wizard prompts, and recipe labels.

- [ ] **Step 3: Create `app/core/i18n/translator.py`**
Implement the `t(key: str, locale: str, **kwargs: Any) -> str` localization lookup helper.

- [ ] **Step 4: Format and lint**
Run `uv run ruff format app/core/` and `uv run ruff check app/core/ --fix`.

---

### Task 2: Database Infrastructure and SQLAlchemy 2.0 Models

**Files:**
- Create: `app/database/session.py`
- Create: `app/database/models/base.py`
- Create: `app/database/models/user.py`
- Create: `app/database/models/category.py`
- Create: `app/database/models/recipe.py`
- Create: `app/database/models/ingredient.py`
- Create: `app/database/models/fridge.py`
- Create: `app/database/models/favorite.py`
- Create: `app/database/models/__init__.py`

**Interfaces:**
- Produces: `Base`, `User`, `Category`, `Recipe`, `Ingredient`, `FridgeItem`, `Favorite`, `get_session_maker()`, `get_async_engine()`

- [ ] **Step 1: Create `app/database/session.py` and `app/database/models/base.py`**
Configure async SQLAlchemy engine with asyncpg, `async_sessionmaker`, and DeclarativeBase with timestamp mixins.

- [ ] **Step 2: Create `User`, `Category`, `Recipe`, `Ingredient`, `FridgeItem`, and `Favorite` models**
Define all database models with foreign keys, relationships, cascade deletes, and indices according to SPEC.md.

- [ ] **Step 3: Create `app/database/models/__init__.py`**
Export all models for discovery by Alembic and repositories.

- [ ] **Step 4: Format and lint**
Run `uv run ruff format app/database/` and `uv run ruff check app/database/ --fix`.

---

### Task 3: Pydantic Schemas & DTOs

**Files:**
- Create: `app/schemas/common.py`
- Create: `app/schemas/category.py`
- Create: `app/schemas/recipe.py`
- Create: `app/schemas/fridge.py`
- Create: `app/schemas/user.py`
- Create: `app/schemas/__init__.py`

**Interfaces:**
- Produces: `SortOrder`, `PaginationParams`, `CategoryDTO`, `RecipeDTO`, `IngredientDTO`, `RecipeCreateDTO`, `RecipeUpdateDTO`, `FridgeItemDTO`, `RecipeMatchResultDTO`, `ParsedRecipeTemplateDTO`, `UserDTO`

- [ ] **Step 1: Implement schemas**
Define strictly-typed Pydantic v2 DTOs with validation rules and converters from SQLAlchemy models.

- [ ] **Step 2: Format and lint**
Run `uv run ruff format app/schemas/` and `uv run ruff check app/schemas/ --fix`.

---

### Task 4: Database Repositories Layer

**Files:**
- Create: `app/database/repositories/base.py`
- Create: `app/database/repositories/user_repo.py`
- Create: `app/database/repositories/category_repo.py`
- Create: `app/database/repositories/recipe_repo.py`
- Create: `app/database/repositories/fridge_repo.py`
- Create: `app/database/repositories/favorite_repo.py`
- Create: `app/database/repositories/__init__.py`

**Interfaces:**
- Produces: `UserRepo`, `CategoryRepo`, `RecipeRepo`, `FridgeRepo`, `FavoriteRepo`

- [ ] **Step 1: Implement base and domain repositories**
Implement async CRUD methods using SQLAlchemy 2.0 select/insert/update/delete expressions with join loading for ingredients, categories, and favorites.

- [ ] **Step 2: Format and lint**
Run `uv run ruff format app/database/repositories/` and `uv run ruff check app/database/repositories/ --fix`.

---

### Task 5: Domain Services Layer

**Files:**
- Create: `app/services/category_service.py`
- Create: `app/services/recipe_service.py`
- Create: `app/services/fridge_service.py`
- Create: `app/services/fridge_matcher_service.py`
- Create: `app/services/media_downloader_service.py`
- Create: `app/services/pdf_export_service.py`
- Create: `app/services/__init__.py`

**Interfaces:**
- Produces: `CategoryService`, `RecipeService`, `FridgeService`, `FridgeMatcherService`, `MediaDownloaderService`, `PdfExportService`

- [ ] **Step 1: Implement CategoryService and RecipeService**
Category tree navigation, category seeding with standard taxonomy, recipe CRUD, scoped in-category search, global search, pagination, and sorting toggle.

- [ ] **Step 2: Implement FridgeService and FridgeMatcherService**
User fridge inventory operations (add, replace, clear, get), string ingredient normalization, 100% full match algorithm, partial 1-2 missing match calculation, and ad-hoc instant ingredient search.

- [ ] **Step 3: Implement MediaDownloaderService and PdfExportService**
Non-blocking async wrappers for `yt-dlp` Instagram video extraction and URL to PDF rendering.

- [ ] **Step 4: Format and lint**
Run `uv run ruff format app/services/` and `uv run ruff check app/services/ --fix`.

---

### Task 6: Bot Middlewares, Filters, and FSM States

**Files:**
- Create: `app/bot/filters/admin.py`
- Create: `app/bot/middlewares/db.py`
- Create: `app/bot/middlewares/auth.py`
- Create: `app/bot/middlewares/i18n.py`
- Create: `app/bot/states/recipe_wizard.py`
- Create: `app/bot/states/search.py`
- Create: `app/bot/states/fridge.py`

**Interfaces:**
- Produces: `IsAdminFilter`, `DbSessionMiddleware`, `AuthMiddleware`, `UserI18nMiddleware`, `RecipeCreateWizard`, `RecipeEditWizard`, `CategorySearchState`, `GlobalSearchState`, `FridgeInputState`

- [ ] **Step 1: Implement filters and middlewares**
Inject `session: AsyncSession`, `user: User`, `locale: str`, and `is_admin: bool` into event data.

- [ ] **Step 2: Implement FSM states**
Define state classes inheriting `StatesGroup` for interactive recipe creation/editing, scoped searching, and fridge batch inputs.

- [ ] **Step 3: Format and lint**
Run `uv run ruff format app/bot/` and `uv run ruff check app/bot/ --fix`.

---

### Task 7: Bot Keyboards & CallbackData Factories

**Files:**
- Create: `app/bot/keyboards/callbacks.py`
- Create: `app/bot/keyboards/catalog.py`
- Create: `app/bot/keyboards/fridge.py`
- Create: `app/bot/keyboards/favorites.py`
- Create: `app/bot/keyboards/admin.py`
- Create: `app/bot/keyboards/common.py`

**Interfaces:**
- Produces: Typed CallbackData models (`CatalogNavCallback`, `RecipeViewCallback`, `SortToggleCallback`, `CategorySearchCallback`, `FridgeActionCallback`, `FavoriteToggleCallback`, `AdminActionCallback`, `LanguageSelectCallback`, `PaginationCallback`), inline builders for all menus and views.

- [ ] **Step 1: Implement callback data factories and inline keyboards**
Construct localized inline keyboards with navigation buttons, pagination controls, sorting toggles, favorite toggles, and admin management actions.

- [ ] **Step 2: Format and lint**
Run `uv run ruff format app/bot/keyboards/` and `uv run ruff check app/bot/keyboards/ --fix`.

---

### Task 8: Bot Routers & Handlers

**Files:**
- Create: `app/bot/handlers/common.py`
- Create: `app/bot/handlers/catalog.py`
- Create: `app/bot/handlers/search.py`
- Create: `app/bot/handlers/fridge.py`
- Create: `app/bot/handlers/favorites.py`
- Create: `app/bot/handlers/admin.py`
- Create: `app/bot/handlers/__init__.py`

**Interfaces:**
- Produces: `common_router`, `catalog_router`, `search_router`, `fridge_router`, `favorites_router`, `admin_router`, `main_router`

- [ ] **Step 1: Implement common router**
`/start`, `/help`, language switcher, main navigation menu.

- [ ] **Step 2: Implement catalog and search routers**
Category navigation, subcategory drill-down, recipe card rendering (with photo, video, PDF, source links), sorting toggle, scoped in-category search, global search, and instant ingredient search.

- [ ] **Step 3: Implement fridge and favorites routers**
Fridge management (view, add, replace, clear), "Ready to Cook" match view, "Almost Ready" match view with missing ingredient callouts, bookmarking favorites, and favorites list pagination.

- [ ] **Step 4: Implement admin router**
Admin dashboard, recipe creation wizard (supporting photo, video, PDF, Instagram URL, web URL), recipe formatted text template parser, recipe editing, recipe deletion, category management.

- [ ] **Step 5: Format and lint**
Run `uv run ruff format app/bot/handlers/` and `uv run ruff check app/bot/handlers/ --fix`.

---

### Task 9: Bot Lifespan, Category Seeder, and Main Entrypoint

**Files:**
- Create: `app/main.py`
- Create: `app/core/seeder.py`

**Interfaces:**
- Produces: `main()`, `seed_initial_categories(session: AsyncSession)`

- [ ] **Step 1: Implement `app/core/seeder.py`**
Seed default 2-level category hierarchy if not already present in database.

- [ ] **Step 2: Implement `app/main.py`**
Configure Bot, Dispatcher, RedisStorage, middlewares, routers, and startup/shutdown lifespan routines.

- [ ] **Step 3: Format and lint**
Run `uv run ruff format app/` and `uv run ruff check app/ --fix`.

---

### Task 10: Graphify Knowledge Graph Refresh & Final Code Quality Check

- [ ] **Step 1: Graphify extract**
Run `graphify extract . --code-only` to refresh the code structure graph.

- [ ] **Step 2: Full lint and format**
Run `uv run ruff format .` and `uv run ruff check . --fix`.
