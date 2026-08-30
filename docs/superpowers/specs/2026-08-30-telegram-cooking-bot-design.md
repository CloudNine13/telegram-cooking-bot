# Design Document: Telegram Cooking & Recipe Management Bot

## 1. Overview
Asynchronous Telegram bot built with Python 3.12+, aiogram 3.x, SQLAlchemy 2.0 (asyncpg), Redis, and PostgreSQL. Enables hierarchical recipe catalog browsing, multi-criteria sorting, scoped and ad-hoc ingredient search, persistent fridge inventory matching (100% and 1-2 missing ingredients), favorites management, multi-language support (EN/RU), and admin catalog curation with automated media/PDF ingestion.

## 2. Architecture & Directory Structure
```
app/
├── core/
│   ├── config.py             # pydantic-settings configuration
│   └── i18n/
│       ├── locales.py        # Locale codes and translation dictionaries (EN/RU)
│       └── translator.py     # Translation helper
├── database/
│   ├── session.py            # Async engine and sessionmaker
│   ├── models/
│   │   ├── base.py           # DeclarativeBase with timestamp mixins
│   │   ├── user.py           # User model (id, username, full_name, language_code)
│   │   ├── category.py       # Hierarchical Category model (parent_id, slugs, names)
│   │   ├── recipe.py         # Recipe model with media references
│   │   ├── ingredient.py     # Ingredient model linked to recipe
│   │   ├── fridge.py         # User FridgeItem model
│   │   └── favorite.py       # User-Recipe Favorite model
│   └── repositories/
│       ├── base.py           # Generic async repository interface
│       ├── user_repo.py      # User persistence and language updates
│       ├── category_repo.py  # Category tree queries and ordering
│       ├── recipe_repo.py    # Recipe queries (filtering, sorting, pagination, search)
│       ├── fridge_repo.py    # User fridge items CRUD
│       └── favorite_repo.py  # Favorites toggle and listing
├── schemas/
│   ├── common.py             # Pagination and SortOrder schemas
│   ├── category.py           # Category DTOs
│   ├── recipe.py             # Recipe, Ingredient DTOs, and ParsedTemplate
│   ├── fridge.py             # Fridge item and match result DTOs
│   └── user.py               # User DTOs
├── services/
│   ├── category_service.py   # Category tree resolution and seed data
│   ├── recipe_service.py     # Recipe business logic, search, and sorting
│   ├── fridge_service.py     # Fridge management (add, replace, clear)
│   ├── fridge_matcher_service.py # 100% and partial (1-2 missing) matching
│   ├── media_downloader_service.py # Background Instagram video extraction (yt-dlp)
│   └── pdf_export_service.py # Background Web-to-PDF conversion
├── bot/
│   ├── filters/
│   │   └── admin.py          # IsAdminFilter
│   ├── middlewares/
│   │   ├── db.py             # DbSessionMiddleware (AsyncSession injection)
│   │   ├── auth.py           # AuthMiddleware (User model & admin status injection)
│   │   └── i18n.py           # UserI18nMiddleware (Locale injection)
│   ├── states/
│   │   ├── recipe_wizard.py  # RecipeCreateWizard, RecipeEditWizard
│   │   ├── search.py         # CategorySearchState, GlobalSearchState
│   │   └── fridge.py         # FridgeInputState
│   ├── keyboards/
│   │   ├── callbacks.py      # Typed CallbackData factories
│   │   ├── catalog.py        # Catalog and recipe inline keyboards
│   │   ├── fridge.py         # Fridge inline keyboards
│   │   ├── favorites.py      # Favorites inline keyboards
│   │   ├── admin.py          # Admin inline keyboards
│   │   └── common.py         # Language select and navigation keyboards
│   └── handlers/
│       ├── common.py         # /start, /help, /language, main navigation
│       ├── catalog.py        # Categories, subcategories, recipe view, sorting
│       ├── search.py         # In-category title search, global search, instant fridge search
│       ├── fridge.py         # Fridge inventory input, 100% match, partial match
│       ├── favorites.py      # Favorite toggle, my favorites list
│       └── admin.py          # Admin menu, recipe wizard, template parser, delete/edit
└── main.py                   # Bot initialization, dispatcher, Redis storage, lifespan
```

## 3. Data Schema & Models
- `users`: `id` (BigInteger, PK), `username` (String, nullable), `full_name` (String, nullable), `language_code` (String, default "en"), `created_at`, `updated_at`.
- `categories`: `id` (Integer, PK), `parent_id` (Integer, FK -> categories.id, nullable), `name_en` (String), `name_ru` (String), `slug` (String, unique), `order_index` (Integer).
- `recipes`: `id` (Integer, PK), `category_id` (Integer, FK -> categories.id), `title_en` (String), `title_ru` (String), `prep_time_minutes` (Integer), `instructions_en` (Text), `instructions_ru` (Text), `photo_file_id` (String, nullable), `video_file_id` (String, nullable), `document_file_id` (String, nullable), `source_url` (String, nullable), `instagram_url` (String, nullable), `created_at`, `updated_at`.
- `ingredients`: `id` (Integer, PK), `recipe_id` (Integer, FK -> recipes.id, ondelete="CASCADE"), `name_en` (String), `name_ru` (String), `normalized_name_en` (String, indexed), `normalized_name_ru` (String, indexed), `quantity` (Float, nullable), `unit` (String, nullable).
- `fridge_items`: `id` (Integer, PK), `user_id` (BigInteger, FK -> users.id, ondelete="CASCADE"), `raw_name` (String), `normalized_name` (String, indexed), `created_at`.
- `favorites`: `id` (Integer, PK), `user_id` (BigInteger, FK -> users.id, ondelete="CASCADE"), `recipe_id` (Integer, FK -> recipes.id, ondelete="CASCADE"), UniqueConstraint(`user_id`, `recipe_id`).

## 4. Key Logic & Flows
1. **Catalog Navigation & Sorting**:
   - Level 1: Main Categories (Breakfast, Soups, Main Dishes, Salads, Appetizers, Desserts, Beverages).
   - Level 2: Subcategories (Main Dishes -> Meat, Fish, Vegetables).
   - Recipes listed with 5 items per page. Toggle between `SortOrder.ALPHABETICAL` (A-Z) and `SortOrder.DATE_ADDED` (Newest first).
2. **In-Category and Global Search**:
   - In-Category: Scoped to selected category/subcategory ID, filters `title ILIKE %query%`.
   - Global Text: Searches across recipe title and ingredient names.
   - Ad-hoc Ingredient Search: Instant match without modifying persistent fridge table.
3. **Fridge Inventory & Matching Algorithm**:
   - Inventory operations: Add (append), Replace all, Clear, View.
   - Normalization: lowercased, stripped punctuation, normalized whitespace.
   - 100% Match: Recipe requires $R$, fridge has $F$, missing $M = R \setminus F = \emptyset$.
   - Partial Match: $|M| \in \{1, 2\}$, recipe card renders missing items with warning icon (`⚠️ Missing: ...`).
4. **Admin Wizard & Media Ingestion**:
   - Step-by-step FSM wizard or raw text template format.
   - Instagram reel URL -> `MediaDownloaderService` triggers async `yt-dlp` download -> uploads to Telegram to retrieve `video_file_id`.
   - External Web URL -> `PdfExportService` renders page to PDF -> uploads to Telegram to retrieve `document_file_id`.
5. **Localization**:
   - Supported languages: `en` (English) and `ru` (Russian).
   - Stored on `User` entity; dynamic string resolution via `t(key, locale, **kwargs)`.
