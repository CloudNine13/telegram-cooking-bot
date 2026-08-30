SUPPORTED_LOCALES: list[str] = [
    "en",
    "ru",
]

DEFAULT_LOCALE: str = "en"

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "welcome": (
            "👋 Welcome to the Cooking & Recipe Bot!\n\n"
            "Discover delicious recipes, search by ingredients, "
            "and match dishes to items in your fridge.\n\n"
            "Use the menu below to start exploring."
        ),
        "help": (
            "📖 Bot Help & Commands:\n\n"
            "/start - Main menu\n"
            "/catalog - Browse recipe catalog\n"
            "/search - Search recipes & ingredients\n"
            "/fridge - Manage fridge & match recipes\n"
            "/favorites - View saved favorite recipes\n"
            "/language - Change language preference\n"
            "/help - Show this help message"
        ),
        "help_admin": (
            "\n\n⚙️ Admin Commands:\n"
            "/admin - Open admin panel\n"
            "/add_recipe - Add a new recipe\n"
            "/manage_categories - Manage categories"
        ),
        "main_menu": "🍽️ Main Menu\nSelect an option below to proceed:",
        "choose_language": "🌐 Select your preferred language:",
        "language_updated": "✅ Language changed to English.",
        "unknown_command": "❓ Unknown command. Use /help to see available options.",
        "action_cancelled": "❌ Action cancelled.",
        "btn_catalog": "📖 Recipe Catalog",
        "btn_search": "🔍 Search",
        "btn_fridge": "🧊 My Fridge",
        "btn_favorites": "⭐ Favorites",
        "btn_language": "🌐 Language",
        "btn_admin": "⚙️ Admin Panel",
        "btn_back": "⬅️ Back",
        "btn_main_menu": "🏠 Main Menu",
        "btn_cancel": "❌ Cancel",
        "btn_skip": "⏩ Skip",
        "btn_prev": "⬅️ Prev",
        "btn_next": "Next ➡️",
        "btn_add_favorite": "⭐ Add to Favorites",
        "btn_remove_favorite": "❌ Remove from Favorites",
        "btn_view_pdf": "📄 Get PDF Guide",
        "btn_view_video": "🎬 Watch Video",
        "btn_source_link": "🔗 Source Webpage",
        "btn_instagram_link": "📸 Instagram Post",
        "btn_sort_alpha": "🔤 Sort: A-Z",
        "btn_sort_date": "🕒 Sort: Newest",
        "btn_search_category": "🔍 Search in Category",
        "btn_search_global": "🌍 Global Search",
        "btn_search_instant": "⚡ Instant Ingredient Search",
        "cat_breakfast": "🍳 Breakfast",
        "cat_soups": "🍲 First Courses / Soups",
        "cat_main_dishes": "🍖 Main Dishes",
        "cat_main_dishes_meat": "🥩 Meat",
        "cat_main_dishes_fish": "🐟 Fish",
        "cat_main_dishes_veg": "🥦 Vegetables",
        "cat_salads": "🥗 Salads",
        "cat_appetizers": "🍢 Appetizers",
        "cat_desserts": "🍰 Desserts",
        "cat_beverages": "🍹 Beverages",
        "catalog_title": "📖 Recipe Catalog\nSelect a category to browse:",
        "catalog_empty": "No recipes found in the catalog.",
        "category_empty": "No recipes found in this category.",
        "subcategory_select": "📂 Select a subcategory:",
        "sort_alpha_active": "🔤 Sorting by: Alphabetical (A-Z)",
        "sort_date_active": "🕒 Sorting by: Date Added (Newest)",
        "recipe_card": (
            "🍳 *{title}*\n\n"
            "⏱️ *Prep Time:* {prep_time} min\n"
            "📂 *Category:* {category}\n\n"
            "🛒 *Ingredients:*\n{ingredients}\n\n"
            "👩‍🍳 *Instructions:*\n{instructions}"
        ),
        "recipe_prep_time": "{minutes} min",
        "recipe_ingredients_header": "🛒 Ingredients:",
        "recipe_instructions_header": "👩‍🍳 Instructions:",
        "recipe_not_found": "❌ Recipe not found.",
        "recipe_missing_ingredients": "⚠️ Missing ingredients ({count}): {items}",
        "recipe_pdf_caption": "📄 Printable recipe guide for *{title}*",
        "recipe_video_caption": "🎬 Video guide for *{title}*",
        "search_menu_title": "🔍 Search Recipes\nChoose search mode:",
        "search_prompt": "🔍 Send recipe title or ingredient to search:",
        "search_in_category_prompt": "🔍 Send search query for category *{category}*:",
        "search_results": "🔍 Found {count} recipe(s) for '{query}':",
        "search_no_results": "❌ No recipes found matching '{query}'.",
        "search_instant_prompt": (
            "⚡ Send comma-separated ingredients to find matching recipes "
            "(e.g. `chicken, garlic, cream`):"
        ),
        "search_instant_results": "⚡ Found {count} matching recipe(s):",
        "search_instant_no_results": "❌ No recipes match the specified ingredients.",
        "fridge_title": "🧊 Your Fridge Inventory",
        "fridge_empty": "Your fridge is currently empty.\nAdd items to get smart recipe suggestions!",
        "fridge_items_list": "🧊 Current items in fridge ({count}):\n{items}",
        "fridge_input_add_prompt": "➕ Send comma-separated items to add to your fridge:",
        "fridge_input_replace_prompt": "🔄 Send comma-separated items to replace your fridge contents:",
        "fridge_added": "✅ Added {count} item(s) to your fridge.",
        "fridge_replaced": "✅ Fridge updated with {count} item(s).",
        "fridge_cleared": "🗑️ Your fridge inventory has been cleared.",
        "btn_fridge_add": "➕ Add Items",
        "btn_fridge_replace": "🔄 Replace All",
        "btn_fridge_clear": "🗑️ Clear Fridge",
        "btn_fridge_match_full": "🍳 Ready to Cook (100% Match)",
        "btn_fridge_match_partial": "🤏 Almost Ready (Missing 1-2)",
        "fridge_match_full_title": "🍳 Ready to Cook (100% Match):",
        "fridge_match_full_empty": "❌ No recipes match 100% of your fridge ingredients.",
        "fridge_match_partial_title": "🤏 Almost Ready (Missing 1-2 items):",
        "fridge_match_partial_empty": "❌ No recipes found missing only 1-2 ingredients.",
        "favorites_title": "⭐ Your Favorite Recipes",
        "favorites_empty": "You have no favorite recipes yet.\nClick ⭐ on any recipe to save it here!",
        "favorite_added": "⭐ Added to favorites!",
        "favorite_removed": "❌ Removed from favorites.",
        "admin_menu": "⚙️ Admin Control Panel\nSelect an action:",
        "admin_unauthorized": "⛔ Access denied. Administrator privileges required.",
        "btn_admin_add_wizard": "➕ Add Recipe (Wizard)",
        "btn_admin_add_template": "📝 Add Recipe (Template)",
        "btn_admin_manage_categories": "📁 Manage Categories",
        "btn_admin_edit_recipe": "✏️ Edit Recipe",
        "btn_admin_delete_recipe": "🗑️ Delete Recipe",
        "admin_recipe_deleted": "✅ Recipe deleted successfully.",
        "admin_recipe_delete_confirm": "⚠️ Are you sure you want to delete *{title}*?",
        "admin_recipe_created": "✅ Recipe *{title}* created successfully!",
        "admin_recipe_updated": "✅ Recipe *{title}* updated successfully!",
        "admin_edit_select_field": "✏️ Edit Recipe *{title}*\nSelect a field to edit:",
        "btn_edit_title_en": "📝 Title (EN)",
        "btn_edit_title_ru": "📝 Title (RU)",
        "btn_edit_category": "📂 Category",
        "btn_edit_prep_time": "⏱️ Prep Time",
        "btn_edit_ingredients": "🛒 Ingredients",
        "btn_edit_instructions_en": "👩‍🍳 Instructions (EN)",
        "btn_edit_instructions_ru": "👩‍🍳 Instructions (RU)",
        "btn_edit_media": "📸 Media & Links",
        "admin_edit_prompt_title_en": "📝 Enter new English title:",
        "admin_edit_prompt_title_ru": "📝 Enter new Russian title:",
        "admin_edit_prompt_category": "📂 Select new category:",
        "admin_edit_prompt_prep_time": "⏱️ Enter new prep time in minutes (number only):",
        "admin_edit_prompt_ingredients": (
            "🛒 Enter new ingredients (one per line, format: `Name - Quantity Unit`):"
        ),
        "admin_edit_prompt_instructions_en": "👩‍🍳 Enter new English cooking instructions:",
        "admin_edit_prompt_instructions_ru": "👩‍🍳 Enter new Russian cooking instructions:",
        "admin_edit_prompt_media": (
            "📸 Send new photo, video, PDF document, URL, or /clear to remove media:"
        ),
        "admin_wizard_title_en": "📝 Step 1/9: Enter recipe title in English:",
        "admin_wizard_title_ru": "📝 Step 2/9: Enter recipe title in Russian:",
        "admin_wizard_category": "📂 Step 3/9: Select category for the recipe:",
        "admin_wizard_prep_time": "⏱️ Step 4/9: Enter prep time in minutes (number only):",
        "admin_wizard_ingredients_en": (
            "🛒 Step 5/9: Enter English ingredients (one per line, format: `Name - Quantity Unit`):"
        ),
        "admin_wizard_ingredients_ru": (
            "🛒 Step 6/9: Enter Russian ingredients (one per line, format: `Name - Quantity Unit`):"
        ),
        "admin_wizard_instructions_en": "👩‍🍳 Step 7/9: Enter English cooking instructions:",
        "admin_wizard_instructions_ru": "👩‍🍳 Step 8/9: Enter Russian cooking instructions:",
        "admin_wizard_photo": "📸 Step 9/9: Send recipe photo or /skip:",
        "admin_wizard_video": "🎬 Optional: Send video file or Instagram Reel URL (or /skip):",
        "admin_wizard_pdf": "📄 Optional: Send PDF file or Web URL (or /skip):",
        "admin_template_prompt": (
            "📝 Send recipe formatted with the template below:\n\n"
            "Title (EN): ...\n"
            "Title (RU): ...\n"
            "Category: ...\n"
            "Prep Time: ...\n"
            "Ingredients (EN):\n"
            "- Item 1\n"
            "Ingredients (RU):\n"
            "- Item 1\n"
            "Instructions (EN):\n"
            "...\n"
            "Instructions (RU):\n"
            "..."
        ),
        "admin_template_invalid": "❌ Failed to parse template. Please check the format and try again.",
        "admin_category_created": "✅ Category *{name}* created successfully.",
        "admin_category_deleted": "✅ Category deleted successfully.",
        "admin_category_prompt_name_en": "📁 Enter category name in English:",
        "admin_category_prompt_name_ru": "📁 Enter category name in Russian:",
        "admin_category_prompt_parent": "📂 Select parent category (or None for top-level):",
        "pagination_page": "Page {current} of {total}",
        "error_occurred": "⚠️ An error occurred while processing your request. Please try again.",
        "error_invalid_number": "⚠️ Please enter a valid positive number.",
    },
    "ru": {
        "welcome": (
            "👋 Добро пожаловать в кулинарный бот!\n\n"
            "Находите вкусные рецепты, ищите блюда по ингредиентам "
            "и подбирайте рецепты под содержимое вашего холодильника.\n\n"
            "Воспользуйтесь меню ниже для начала."
        ),
        "help": (
            "📖 Справка и команды бота:\n\n"
            "/start - Главное меню\n"
            "/catalog - Каталог рецептов\n"
            "/search - Поиск рецептов и продуктов\n"
            "/fridge - Мой холодильник и подбор блюд\n"
            "/favorites - Избранные рецепты\n"
            "/language - Смена языка\n"
            "/help - Показать эту справку"
        ),
        "help_admin": (
            "\n\n⚙️ Команды администратора:\n"
            "/admin - Панель управления\n"
            "/add_recipe - Добавить рецепт\n"
            "/manage_categories - Управление категориями"
        ),
        "main_menu": "🍽️ Главное меню\nВыберите нужный раздел:",
        "choose_language": "🌐 Выберите язык интерфейса:",
        "language_updated": "✅ Язык изменен на русский.",
        "unknown_command": "❓ Неизвестная команда. Введите /help для списка доступных команд.",
        "action_cancelled": "❌ Действие отменено.",
        "btn_catalog": "📖 Каталог рецептов",
        "btn_search": "🔍 Поиск",
        "btn_fridge": "🧊 Мой холодильник",
        "btn_favorites": "⭐ Избранное",
        "btn_language": "🌐 Язык",
        "btn_admin": "⚙️ Админ-панель",
        "btn_back": "⬅️ Назад",
        "btn_main_menu": "🏠 Главное меню",
        "btn_cancel": "❌ Отмена",
        "btn_skip": "⏩ Пропустить",
        "btn_prev": "⬅️ Назад",
        "btn_next": "Вперед ➡️",
        "btn_add_favorite": "⭐ В избранное",
        "btn_remove_favorite": "❌ Удалить из избранного",
        "btn_view_pdf": "📄 Скачать PDF",
        "btn_view_video": "🎬 Смотреть видео",
        "btn_source_link": "🔗 Источник",
        "btn_instagram_link": "📸 Инстаграм",
        "btn_sort_alpha": "🔤 Сортировка: А-Я",
        "btn_sort_date": "🕒 Сортировка: Новые",
        "btn_search_category": "🔍 Искать в категории",
        "btn_search_global": "🌍 Глобальный поиск",
        "btn_search_instant": "⚡ Быстрый поиск по ингредиентам",
        "cat_breakfast": "🍳 Завтрак",
        "cat_soups": "🍲 Первые блюда",
        "cat_main_dishes": "🍖 Вторые блюда",
        "cat_main_dishes_meat": "🥩 Мясо",
        "cat_main_dishes_fish": "🐟 Рыба",
        "cat_main_dishes_veg": "🥦 Овощи",
        "cat_salads": "🥗 Салаты",
        "cat_appetizers": "🍢 Закуски",
        "cat_desserts": "🍰 Десерты",
        "cat_beverages": "🍹 Напитки",
        "catalog_title": "📖 Каталог рецептов\nВыберите категорию:",
        "catalog_empty": "В каталоге пока нет рецептов.",
        "category_empty": "В этой категории пока нет рецептов.",
        "subcategory_select": "📂 Выберите подкатегорию:",
        "sort_alpha_active": "🔤 Сортировка: По алфавиту (А-Я)",
        "sort_date_active": "🕒 Сортировка: По дате (Сначала новые)",
        "recipe_card": (
            "🍳 *{title}*\n\n"
            "⏱️ *Время приготовления:* {prep_time} мин\n"
            "📂 *Категория:* {category}\n\n"
            "🛒 *Ингредиенты:*\n{ingredients}\n\n"
            "👩‍🍳 *Инструкции:*\n{instructions}"
        ),
        "recipe_prep_time": "{minutes} мин",
        "recipe_ingredients_header": "🛒 Ингредиенты:",
        "recipe_instructions_header": "👩‍🍳 Инструкции:",
        "recipe_not_found": "❌ Рецепт не найден.",
        "recipe_missing_ingredients": "⚠️ Не хватает ингредиентов ({count}): {items}",
        "recipe_pdf_caption": "📄 Рецепт в формате PDF: *{title}*",
        "recipe_video_caption": "🎬 Видео рецепта: *{title}*",
        "search_menu_title": "🔍 Поиск рецептов\nВыберите режим поиска:",
        "search_prompt": "🔍 Введите название блюда или ингредиенты:",
        "search_in_category_prompt": "🔍 Введите поисковый запрос для категории *{category}*:",
        "search_results": "🔍 Найдено {count} рецепт(ов) по запросу '{query}':",
        "search_no_results": "❌ По запросу '{query}' ничего не найдено.",
        "search_instant_prompt": (
            "⚡ Введите ингредиенты через запятую для быстрого поиска "
            "(например: `курица, чеснок, сливки`):"
        ),
        "search_instant_results": "⚡ Найдено {count} подходящих рецепт(ов):",
        "search_instant_no_results": "❌ По заданным ингредиентам ничего не найдено.",
        "fridge_title": "🧊 Содержимое вашего холодильника",
        "fridge_empty": "Ваш холодильник пуст.\nДобавьте продукты, чтобы получать умные рекомендации!",
        "fridge_items_list": "🧊 Продукты в холодильнике ({count}):\n{items}",
        "fridge_input_add_prompt": "➕ Отправьте список продуктов через запятую для добавления:",
        "fridge_input_replace_prompt": "🔄 Отправьте список продуктов через запятую для полной замены:",
        "fridge_added": "✅ В холодильник добавлено {count} продукт(ов).",
        "fridge_replaced": "✅ Холодильник обновлен, всего продуктов: {count}.",
        "fridge_cleared": "🗑️ Холодильник полностью очищен.",
        "btn_fridge_add": "➕ Добавить продукты",
        "btn_fridge_replace": "🔄 Заменить все",
        "btn_fridge_clear": "🗑️ Очистить холодильник",
        "btn_fridge_match_full": "🍳 Можно готовить (100% совпадение)",
        "btn_fridge_match_partial": "🤏 Почти готово (не хватает 1-2)",
        "fridge_match_full_title": "🍳 Можно готовить прямо сейчас (100% совпадение):",
        "fridge_match_full_empty": "❌ Нет рецептов со 100% совпадением продуктов из холодильника.",
        "fridge_match_partial_title": "🤏 Почти готово (не хватает 1-2 ингредиентов):",
        "fridge_match_partial_empty": "❌ Нет рецептов с нехваткой 1-2 ингредиентов.",
        "favorites_title": "⭐ Ваши избранные рецепты",
        "favorites_empty": "В избранном пока ничего нет.\nНажмите ⭐ на карточке любого рецепта!",
        "favorite_added": "⭐ Рецепт добавлен в избранное!",
        "favorite_removed": "❌ Рецепт удален из избранного.",
        "admin_menu": "⚙️ Панель администратора\nВыберите действие:",
        "admin_unauthorized": "⛔ Доступ запрещен. Требуются права администратора.",
        "btn_admin_add_wizard": "➕ Добавить рецепт (Пошагово)",
        "btn_admin_add_template": "📝 Добавить рецепт (Шаблон)",
        "btn_admin_manage_categories": "📁 Управление категориями",
        "btn_admin_edit_recipe": "✏️ Редактировать рецепт",
        "btn_admin_delete_recipe": "🗑️ Удалить рецепт",
        "admin_recipe_deleted": "✅ Рецепт успешно удален.",
        "admin_recipe_delete_confirm": "⚠️ Вы уверены, что хотите удалить *{title}*?",
        "admin_recipe_created": "✅ Рецепт *{title}* успешно создан!",
        "admin_recipe_updated": "✅ Рецепт *{title}* успешно обновлен!",
        "admin_edit_select_field": "✏️ Редактирование рецепта *{title}*\nВыберите поле для изменения:",
        "btn_edit_title_en": "📝 Название (EN)",
        "btn_edit_title_ru": "📝 Название (RU)",
        "btn_edit_category": "📂 Категория",
        "btn_edit_prep_time": "⏱️ Время готовки",
        "btn_edit_ingredients": "🛒 Ингредиенты",
        "btn_edit_instructions_en": "👩‍🍳 Инструкция (EN)",
        "btn_edit_instructions_ru": "👩‍🍳 Инструкция (RU)",
        "btn_edit_media": "📸 Медиа и ссылки",
        "admin_edit_prompt_title_en": "📝 Введите новое название на английском:",
        "admin_edit_prompt_title_ru": "📝 Введите новое название на русском:",
        "admin_edit_prompt_category": "📂 Выберите новую категорию:",
        "admin_edit_prompt_prep_time": "⏱️ Введите новое время приготовления в минутах (только число):",
        "admin_edit_prompt_ingredients": (
            "🛒 Введите новые ингредиенты (по одному на строку, формат: `Название - Количество Ед`):"
        ),
        "admin_edit_prompt_instructions_en": "👩‍🍳 Введите новые шаги приготовления на английском:",
        "admin_edit_prompt_instructions_ru": "👩‍🍳 Введите новые шаги приготовления на русском:",
        "admin_edit_prompt_media": (
            "📸 Отправьте новое фото, видео, PDF документ, ссылку или /clear для удаления медиа:"
        ),
        "admin_wizard_title_en": "📝 Шаг 1/9: Введите название рецепта на английском:",
        "admin_wizard_title_ru": "📝 Шаг 2/9: Введите название рецепта на русском:",
        "admin_wizard_category": "📂 Шаг 3/9: Выберите категорию для рецепта:",
        "admin_wizard_prep_time": "⏱️ Шаг 4/9: Введите время приготовления в минутах (только число):",
        "admin_wizard_ingredients_en": (
            "🛒 Шаг 5/9: Введите ингредиенты на английском (по одному на строку, формат: `Название - Количество Ед`):"
        ),
        "admin_wizard_ingredients_ru": (
            "🛒 Шаг 6/9: Введите ингредиенты на русском (по одному на строку, формат: `Название - Количество Ед`):"
        ),
        "admin_wizard_instructions_en": "👩‍🍳 Шаг 7/9: Введите шаги приготовления на английском:",
        "admin_wizard_instructions_ru": "👩‍🍳 Шаг 8/9: Введите шаги приготовления на русском:",
        "admin_wizard_photo": "📸 Шаг 9/9: Отправьте фото блюда или /skip:",
        "admin_wizard_video": "🎬 Опционально: Отправьте видео или ссылку на Instagram Reel (или /skip):",
        "admin_wizard_pdf": "📄 Опционально: Отправьте PDF файл или ссылку на веб-страницу (или /skip):",
        "admin_template_prompt": (
            "📝 Отправьте рецепт по шаблону:\n\n"
            "Title (EN): ...\n"
            "Title (RU): ...\n"
            "Category: ...\n"
            "Prep Time: ...\n"
            "Ingredients (EN):\n"
            "- Продукт 1\n"
            "Ingredients (RU):\n"
            "- Продукт 1\n"
            "Instructions (EN):\n"
            "...\n"
            "Instructions (RU):\n"
            "..."
        ),
        "admin_template_invalid": "❌ Не удалось разобрать шаблон. Проверьте формат и попробуйте снова.",
        "admin_category_created": "✅ Категория *{name}* успешно создана.",
        "admin_category_deleted": "✅ Категория успешно удалена.",
        "admin_category_prompt_name_en": "📁 Введите название категории на английском:",
        "admin_category_prompt_name_ru": "📁 Введите название категории на русском:",
        "admin_category_prompt_parent": "📂 Выберите родительскую категорию (или Нет для верхнего уровня):",
        "pagination_page": "Страница {current} из {total}",
        "error_occurred": "⚠️ Произошла ошибка при обработке запроса. Пожалуйста, попробуйте снова.",
        "error_invalid_number": "⚠️ Введите корректное положительное число.",
    },
}
