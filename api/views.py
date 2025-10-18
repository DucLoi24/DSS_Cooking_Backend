from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q
# Import các công cụ để bắt lỗi
from django.db import utils
from rest_framework.exceptions import ValidationError

from .models import Recipes, PantryItems, Ingredients, RecipeIngredients, ShoppingListItems, FavoriteRecipes
from django.contrib.auth.models import User
from .serializers import (
    RecipeSerializer, UserSerializer, 
    PantryItemReadSerializer, PantryItemWriteSerializer,
    IngredientSerializer, RecipeCreateSerializer, MyRecipeSerializer,
    RecipeDetailSerializer, ShoppingListItemSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView

# --- CÁC VIEW CŨ (Không thay đổi) ---
# ... (UserRegisterView, LoginView, etc. giữ nguyên)
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class LoginView(TokenObtainPairView):
    pass

class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user

class IngredientListCreateView(generics.ListCreateAPIView):
    queryset = Ingredients.objects.filter(status='approved')
    serializer_class = IngredientSerializer
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user, status='pending')

class RecipeListCreateView(generics.ListCreateAPIView):
    queryset = Recipes.objects.filter(status='public')
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecipeCreateSerializer
        return RecipeSerializer
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
    def perform_create(self, serializer):
        serializer.save(author=self.request.user, status='private')

class RecipeDetailUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeDetailSerializer
        return RecipeCreateSerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    def get_queryset(self):
        user = self.request.user
        if self.request.method == 'GET':
            if user.is_authenticated:
                return Recipes.objects.filter(Q(status='public') | Q(author=user)).distinct()
            else:
                return Recipes.objects.filter(status='public')
        return Recipes.objects.filter(author=user)

class MyRecipeListView(generics.ListAPIView):
    serializer_class = MyRecipeSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Recipes.objects.filter(author=self.request.user).order_by('-created_at')

class SubmitReviewView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, format=None):
        try:
            recipe = Recipes.objects.get(pk=pk)
        except Recipes.DoesNotExist:
            return Response({'error': 'Công thức không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        if recipe.author != request.user:
            return Response({'error': 'Bạn không có quyền thực hiện hành động này.'}, status=status.HTTP_403_FORBIDDEN)
        if recipe.status != 'private':
                return Response({'error': 'Công thức này đã được gửi hoặc đã công khai.'}, status=status.HTTP_400_BAD_REQUEST)
        recipe.status = 'pending_approval'
        recipe.save()
        return Response({'message': 'Công thức đã được gửi đi để duyệt thành công.'}, status=status.HTTP_200_OK)

# --- "CÁI BẪY" ĐƯỢC ĐẶT Ở ĐÂY ---
class PantryView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PantryItemWriteSerializer
        return PantryItemReadSerializer
        
    def get_queryset(self):
        return PantryItems.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        ingredient_id = request.data.get('ingredient')
        quantity = request.data.get('quantity')
        user = request.user

        if not ingredient_id:
            return Response({'error': 'Ingredient ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        print("\n--- BẮT ĐẦU CHIẾN DỊCH ĐẶT BẪY TỦ LẠNH ---")
        print(f"User: {user.id}, Ingredient ID: {ingredient_id}, Quantity: {quantity}")
        
        try:
            # Chúng ta sẽ thử thực hiện hành động nguy hiểm này
            print("Đang chuẩn bị gọi update_or_create...")
            pantry_item, created = PantryItems.objects.update_or_create(
                user=user,
                ingredient_id=ingredient_id,
                defaults={'quantity': quantity}
            )
            print("--- LƯU THÀNH CÔNG! ---")
            
            serializer = PantryItemReadSerializer(pantry_item)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            print("--- HOÀN TẤT, CHUẨN BỊ GỬI RESPONSE ---\n")
            return Response(serializer.data, status=status_code)

        except utils.IntegrityError as e:
            # BẪY SẬP! Bắt được lỗi ràng buộc database
            print("--- BẪY SẬP! BẮT ĐƯỢC LỖI INTEGRITYERROR ---")
            print(f"LỜI KHAI CỦA DATABASE: {e}")
            print("KẾT LUẬN: Rất có thể ingredient_id không hợp lệ hoặc một ràng buộc khác bị vi phạm.")
            print("--- KẾT THÚC BÁO CÁO ---\n")
            raise ValidationError({'database_error': f"Lỗi ràng buộc CSDL: {e}"})
        
        except Exception as e:
            # BẪY SẬP! Bắt được một lỗi chung chung khác
            print("--- BẪY SẬP! BẮT ĐƯỢC MỘT LỖI KHÁC ---")
            print(f"LOẠI LỖI: {type(e)}")
            print(f"CHI TIẾT LỖI: {e}")
            print("--- KẾT THÚC BÁO CÁO ---\n")
            raise e

class PantryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PantryItemWriteSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PantryItems.objects.filter(user=self.request.user)

class SuggestionView(generics.ListAPIView):
    # ... (giữ nguyên)
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        pantry_ingredient_ids = PantryItems.objects.filter(user=user).values_list('ingredient_id', flat=True)
        if not pantry_ingredient_ids:
            return Recipes.objects.none()
        searchable_recipes = Recipes.objects.filter(
            Q(status='public') | Q(author=user)
        ).distinct()
        recipes_with_missing_count = searchable_recipes.annotate(
            missing_ingredients_count=Count(
                'ingredients',
                filter=~Q(ingredients__ingredient_id__in=pantry_ingredient_ids)
            )
        )
        suggested_recipes = recipes_with_missing_count.filter(missing_ingredients_count__lte=2)
        ranked_recipes = suggested_recipes.annotate(
            pantry_match_count=Count(
                'ingredients',
                filter=Q(ingredients__ingredient_id__in=pantry_ingredient_ids)
            )
        ).order_by('missing_ingredients_count', '-pantry_match_count')
        return ranked_recipes

# --- CÁC VIEW CÒN LẠI (giữ nguyên) ---
# ... (FavoriteToggleView, FavoriteListView, ShoppingListView, ShoppingListDetailView)
class FavoriteToggleView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk, format=None):
        try:
            recipe = Recipes.objects.get(pk=pk)
        except Recipes.DoesNotExist:
            return Response({'error': 'Công thức không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        favorite, created = FavoriteRecipes.objects.get_or_create(user=self.request.user, recipe=recipe)
        if created:
            return Response({'message': 'Đã thêm vào danh sách yêu thích.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Công thức này đã có trong danh sách yêu thích.'}, status=status.HTTP_200_OK)
    def delete(self, request, pk, format=None):
        try:
            favorite = FavoriteRecipes.objects.get(user=self.request.user, recipe_id=pk)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FavoriteRecipes.DoesNotExist:
            return Response({'error': 'Công thức này không có trong danh sách yêu thích của bạn.'}, status=status.HTTP_404_NOT_FOUND)

class FavoriteListView(generics.ListAPIView):
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        favorite_recipe_ids = FavoriteRecipes.objects.filter(user=user).values_list('recipe_id', flat=True)
        return Recipes.objects.filter(id__in=favorite_recipe_ids)

class ShoppingListView(generics.ListCreateAPIView):
    serializer_class = ShoppingListItemSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return ShoppingListItems.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_checked=False)

class ShoppingListDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShoppingListItemSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return ShoppingListItems.objects.filter(user=self.request.user)