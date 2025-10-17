from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RecipeListCreateView, RecipeDetailUpdateDestroyView, UserRegisterView, LoginView, PantryView, UserDetailView, IngredientListCreateView, PantryDetailView, MyRecipeListView, SubmitReviewView, SuggestionView, FavoriteToggleView, FavoriteListView, ShoppingListView, ShoppingListDetailView

urlpatterns = [
    # Các đường dẫn API

    # Địa chỉ cho công thức
    path('recipes/', RecipeListCreateView.as_view(), name='recipe-list-create'),
    path('recipes/<int:pk>/', RecipeDetailUpdateDestroyView.as_view(), name='recipe-detail-update-destroy'),
    path('recipes/my-recipes/', MyRecipeListView.as_view(), name='my-recipe-list'),
    path('recipes/<int:pk>/submit-review/', SubmitReviewView.as_view(), name='submit-review'),
    path('recipes/<int:pk>/favorite/', FavoriteToggleView.as_view(), name='recipe-favorite-toggle'),
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),

    # Địa chỉ cho danh sách mua sắm
    path('shopping-list/', ShoppingListView.as_view(), name='shopping-list'),
    path('shopping-list/<int:pk>/', ShoppingListDetailView.as_view(), name='shopping-list-detail'),

    # Địa chỉ cho người dùng
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('users/me/', UserDetailView.as_view(), name='user-detail'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Địa chỉ cho tủ lạnh (Pantry)
    path('pantry/', PantryView.as_view(), name='pantry'),
    path('pantry/<int:pk>/', PantryDetailView.as_view(), name='pantry-detail'),

    # Địa chỉ cho nguyên liệu (Ingredients)
    path('ingredients/', IngredientListCreateView.as_view(), name='ingredient-list'),

    # Địa chỉ cho công cụ đề xuất
    path('suggestions/', SuggestionView.as_view(), name='suggestions'),
]