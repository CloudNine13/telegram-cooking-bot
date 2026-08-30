# Bilingual Recipe Card Title Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display bilingual recipe names in the format "Russian / English" specifically within recipe cards, while maintaining single localized titles in list views, dialogs, and media captions.

**Architecture:** Add a dedicated title formatting helper in the catalog handler module and update recipe card formatting to construct the dual title string before HTML escaping.

**Tech Stack:** Python 3.12, aiogram 3.x, Pydantic v2, Ruff

## Global Constraints
- Strictly follow PEP 8 and Python 3.12+ typing standards.
- No comments or docstrings in proprietary code.
- Trailing commas in multiline expressions.
- Keep line lengths under 80 characters where possible.
- Lint and format using `uv run ruff check . --fix` and `uv run ruff format .`.

---

### Task 1: Update Recipe Card Title Formatting

**Files:**
- Modify: `app/bot/handlers/catalog.py:75-117`

**Interfaces:**
- Consumes: `RecipeDTO.title` (`dict[str, str]`), `get_localized_text(data, locale)`
- Produces: `_format_recipe_title(title_dict, locale) -> str`, `_format_recipe_card(recipe, locale) -> str`

- [x] **Step 1: Implement `_format_recipe_title` helper and update `_format_recipe_card` in `app/bot/handlers/catalog.py`**

- [x] **Step 2: Run linter and formatter**

Run:
```bash
uv run ruff check . --fix
uv run ruff format .
```

- [x] **Step 3: Commit changes**

```bash
git add app/bot/handlers/catalog.py docs/superpowers/plans/2026-08-30-recipe-card-bilingual-title.md
git commit -m "feat(catalog): display bilingual title Russian / English in recipe cards"
```
