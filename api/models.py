from django.conf import settings
from django.db import models

# Các model nội bộ của Django không cần định nghĩa ở đây

class Ingredients(models.Model):
    # Định nghĩa các lựa chọn cho status theo chuẩn Django
    class Status(models.TextChoices):
        PENDING = 'pending_approval', 'Chờ duyệt'
        APPROVED = 'approved', 'Đã duyệt'
        REJECTED = 'rejected', 'Bị từ chối'

    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, db_column='submitted_by_id', blank=True, null=True)
    
    # Sửa TextField thành CharField với choices, khớp với ENUM trong CSDL
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ingredients'

class Recipes(models.Model):
    # Định nghĩa các lựa chọn cho status và difficulty
    class Status(models.TextChoices):
        PRIVATE = 'private', 'Riêng tư'
        PENDING = 'pending_approval', 'Chờ duyệt'
        PUBLIC = 'public', 'Công khai'
        REJECTED = 'rejected', 'Bị từ chối'

    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Dễ'
        MEDIUM = 'medium', 'Trung bình'
        HARD = 'hard', 'Khó'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    instructions = models.TextField()
    
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.EASY
    )
    
    cooking_time_minutes = models.IntegerField(blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, db_column='author_id')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRIVATE
    )
    
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipes'

class PantryItems(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, blank=True, null=True)
    ingredient = models.ForeignKey(Ingredients, models.DO_NOTHING, blank=True, null=True)
    quantity = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pantry_items'

class RecipeIngredients(models.Model):
    recipe = models.ForeignKey('Recipes', related_name='ingredients', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredients, models.DO_NOTHING)
    quantity = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_ingredients'
        unique_together = (('recipe', 'ingredient'),)

class ShoppingListItems(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, blank=True, null=True)
    ingredient = models.ForeignKey(Ingredients, models.DO_NOTHING, blank=True, null=True)
    is_checked = models.BooleanField(blank=True, null=True)
    quantity = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'shopping_list_items'

class FavoriteRecipes(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, models.DO_NOTHING, primary_key=True)
    recipe = models.ForeignKey('Recipes', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'favorite_recipes'
        unique_together = (('user', 'recipe'),)