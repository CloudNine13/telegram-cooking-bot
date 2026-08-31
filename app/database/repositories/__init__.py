from app.database.repositories.base import BaseRepo
from app.database.repositories.category_repo import CategoryRepo
from app.database.repositories.favorite_repo import FavoriteRepo
from app.database.repositories.fridge_repo import FridgeRepo
from app.database.repositories.recipe_repo import RecipeRepo
from app.database.repositories.user_repo import UserRepo

__all__: list[str] = [
    "BaseRepo",
    "CategoryRepo",
    "FavoriteRepo",
    "FridgeRepo",
    "RecipeRepo",
    "UserRepo",
]
