# api/admin.py
from django.contrib import admin
from .models import (
    Recipes, Ingredients, PantryItems, 
    RecipeIngredients, ShoppingListItems, FavoriteRecipes
)

# --- TÙY CHỈNH CHO TRANG QUẢN LÝ CÔNG THỨC ---
@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    # Hiển thị các cột này trong danh sách
    list_display = ('title', 'author', 'status', 'created_at')
    # Thêm bộ lọc bên cạnh
    list_filter = ('status', 'difficulty')
    # Thêm thanh tìm kiếm
    search_fields = ('title', 'author__username')
    # Định nghĩa các "vũ khí" - các hàm hành động
    actions = ['make_public', 'make_rejected']

    # Hàm hành động để duyệt
    def make_public(self, request, queryset):
        # queryset chứa tất cả các đối tượng đã được chọn
        updated_count = queryset.update(status='public')
        self.message_user(request, f"{updated_count} công thức đã được duyệt và công khai.")
    make_public.short_description = "Duyệt và Công khai các Công thức đã chọn"

    # Hàm hành động để từ chối
    def make_rejected(self, request, queryset):
        updated_count = queryset.update(status='rejected')
        self.message_user(request, f"{updated_count} công thức đã bị từ chối.")
    make_rejected.short_description = "Từ chối các Công thức đã chọn"


# --- TÙY CHỈNH CHO TRANG QUẢN LÝ NGUYÊN LIỆU ---
@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitted_by', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'submitted_by__username')
    actions = ['make_approved', 'make_rejected']

    # Hàm hành động để duyệt
    def make_approved(self, request, queryset):
        updated_count = queryset.update(status='approved')
        self.message_user(request, f"{updated_count} nguyên liệu đã được duyệt.")
    make_approved.short_description = "Duyệt các Nguyên liệu đã chọn"

    # Hàm hành động để từ chối
    def make_rejected(self, request, queryset):
        updated_count = queryset.update(status='rejected')
        self.message_user(request, f"{updated_count} nguyên liệu đã bị từ chối.")
    make_rejected.short_description = "Từ chối các Nguyên liệu đã chọn"

admin.site.register(RecipeIngredients)