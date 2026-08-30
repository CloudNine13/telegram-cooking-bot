from aiogram.fsm.state import State, StatesGroup


class RecipeCreateWizard(StatesGroup):
    title_en: State = State()
    title_ru: State = State()
    category_id: State = State()
    prep_time: State = State()
    ingredients_en: State = State()
    ingredients_ru: State = State()
    instructions_en: State = State()
    instructions_ru: State = State()
    photo: State = State()
    video: State = State()
    pdf: State = State()
    confirmation: State = State()


class RecipeEditWizard(StatesGroup):
    select_field: State = State()
    title_en: State = State()
    title_ru: State = State()
    category_id: State = State()
    prep_time: State = State()
    ingredients_en: State = State()
    ingredients_ru: State = State()
    instructions_en: State = State()
    instructions_ru: State = State()
    photo: State = State()
    video: State = State()
    pdf: State = State()
    source_url: State = State()
    instagram_url: State = State()


class RecipeTemplateImportState(StatesGroup):
    waiting_for_template: State = State()


class CategoryCreateWizard(StatesGroup):
    name_en: State = State()
    name_ru: State = State()
    parent_id: State = State()
