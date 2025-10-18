from rest_framework import serializers
from .models import Recipes, PantryItems, Ingredients, RecipeIngredients, ShoppingListItems, FavoriteRecipes
from django.contrib.auth.models import User

# --- SERIALIZER CHO CÔNG THỨC CÔNG KHAI ---
class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = ['id', 'title', 'description', 'difficulty', 'cooking_time_minutes', 'instructions']

# --- SERIALIZER CHO CÔNG THỨC CÁ NHÂN ---
class MyRecipeSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['status']

# --- SERIALIZER CHO CHI TIẾT NGUYÊN LIỆU TRONG CÔNG THỨC ---
class RecipeIngredientDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)

    class Meta:
        model = RecipeIngredients
        fields = ['id', 'name', 'quantity', 'unit']

# --- SERIALIZER CAO CẤP CHO TRANG CHI TIẾT CÔNG THỨC ---
class RecipeDetailSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientDetailSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Recipes
        fields = ['id', 'title', 'description', 'instructions', 'difficulty', 'cooking_time_minutes', 'author_name', 'ingredients']

# --- SERIALIZER ĐỂ TẠO CÔNG THỨC MỚI ---
class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredients
        fields = ['ingredient', 'quantity', 'unit']

class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Recipes
        fields = ['id', 'title', 'description', 'instructions', 'difficulty', 'cooking_time_minutes', 'ingredients']

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipes.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            RecipeIngredients.objects.create(recipe=recipe, **ingredient_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.instructions = validated_data.get('instructions', instance.instructions)
        instance.difficulty = validated_data.get('difficulty', instance.difficulty)
        instance.cooking_time_minutes = validated_data.get('cooking_time_minutes', instance.cooking_time_minutes)
        instance.save()
        
        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredients.objects.create(recipe=instance, **ingredient_data)
        return instance

# --- SERIALIZERS CHO USER ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=True
        )
        return user

# --- SERIALIZERS CHO TỦ LẠNH ---
class PantryItemReadSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_id = serializers.IntegerField(source='ingredient.id', read_only=True)
    class Meta:
        model = PantryItems
        fields = ['id', 'ingredient_id', 'ingredient_name', 'quantity']

class PantryItemWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PantryItems
        fields = ['id', 'ingredient', 'quantity']

# --- SERIALIZERS CHO DANH SÁCH MUA SẮM ---
class ShoppingListItemSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    class Meta:
        model = ShoppingListItems
        fields = ['id', 'ingredient', 'ingredient_name', 'is_checked', 'quantity']
        read_only_fields = ['id', 'ingredient_name']

# --- SERIALIZER CHO NGUYÊN LIỆU ---
class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ['id', 'name', 'description']

class IngredientContributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        # Cho phép người dùng gửi lên 3 trường này
        fields = ['name', 'description', 'category']