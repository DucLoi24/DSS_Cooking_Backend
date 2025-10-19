from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q, F, Case, When, FloatField, Sum, Value
# Import các công cụ để bắt lỗi
from django.db import utils
from rest_framework.exceptions import ValidationError

from .models import Recipes, PantryItems, Ingredients, RecipeIngredients, ShoppingListItems, FavoriteRecipes
from django.contrib.auth.models import User
from .serializers import (
    RecipeSerializer, UserSerializer, 
    PantryItemReadSerializer, PantryItemWriteSerializer,
    IngredientSerializer, RecipeCreateSerializer, MyRecipeSerializer,
    RecipeDetailSerializer, ShoppingListItemSerializer, IngredientContributeSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView

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
    
    # Dùng serializer khác nhau cho việc đọc và ghi
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IngredientContributeSerializer
        return IngredientSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
        
    def perform_create(self, serializer):
        # Logic không đổi, serializer đã lo việc lấy 'category'
        serializer.save(submitted_by=self.request.user, status='pending')

class RecipeListCreateView(generics.ListCreateAPIView):
    queryset = Recipes.objects.filter(status='public')
    
    # Kích hoạt các bộ lọc
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Các trường có thể lọc chính xác (ví dụ: /api/recipes/?difficulty=easy)
    filterset_fields = ['difficulty', 'author']
    
    # Các trường có thể tìm kiếm (ví dụ: /api/recipes/?search=bò kho)
    # ^: tìm kiếm bắt đầu bằng, =: khớp chính xác, @: tìm kiếm toàn văn, $: regex
    search_fields = ['title', 'description', 'ingredients__ingredient__name']
    
    # Các trường có thể sắp xếp (ví dụ: /api/recipes/?ordering=-created_at)
    ordering_fields = ['cooking_time_minutes', 'created_at']

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
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        mode = self.request.query_params.get('mode', 'strict')
        pantry_ingredient_ids = list(PantryItems.objects.filter(user=user).values_list('ingredient_id', flat=True))

        if not pantry_ingredient_ids:
            return Recipes.objects.none()

        favorite_author_ids = list(FavoriteRecipes.objects.filter(user=user).values_list('recipe__author_id', flat=True).distinct())

        WEIGHTS = {
            Ingredients.Category.PROTEIN: 100,
            Ingredients.Category.CARB: 80,
            Ingredients.Category.VEGETABLE: 50,
            Ingredients.Category.SPICE: 10,
            Ingredients.Category.OTHER: 25,
        }
        when_expressions = [When(ingredients__ingredient__category=cat, then=Value(weight)) for cat, weight in WEIGHTS.items()]

        searchable_recipes = Recipes.objects.filter(Q(status='public') | Q(author=user)).distinct()

        # --- "CHIẾN LƯỢC MỚI: CHIA ĐỂ TRỊ" ---
        # BƯỚC 1: Annotate từng thành phần điểm số một cách riêng lẻ
        recipes_with_components = searchable_recipes.annotate(
            match_count=Count('ingredients', filter=Q(ingredients__ingredient_id__in=pantry_ingredient_ids) & ~Q(ingredients__ingredient__category=Ingredients.Category.STAPLE)),
            missing_penalty_score=Sum(
                Case(*when_expressions, default=Value(25.0), output_field=FloatField()),
                filter=~Q(ingredients__ingredient_id__in=pantry_ingredient_ids) & ~Q(ingredients__ingredient__category=Ingredients.Category.STAPLE),
                default=Value(0.0)
            ),
            author_bonus=Case(
                When(author_id__in=favorite_author_ids, then=Value(50.0)),
                default=Value(0.0),
                output_field=FloatField()
            ),
            missing_count=Count('ingredients', filter=~Q(ingredients__ingredient_id__in=pantry_ingredient_ids) & ~Q(ingredients__ingredient__category=Ingredients.Category.STAPLE))
        )

        # BƯỚC 2: Dùng một annotate cuối cùng, đơn giản, chỉ để tính toán
        # từ các thành phần đã được annotate ở trên.
        recipes_with_final_score = recipes_with_components.annotate(
            score=(
                (F('match_count') * Value(20.0)) - F('missing_penalty_score') + F('author_bonus')
            )
        )
        
        # BƯỚC 3: Lọc và sắp xếp như cũ
        if mode == 'strict':
            final_recipes = recipes_with_final_score.filter(missing_count=0)
        else:
            final_recipes = recipes_with_final_score.filter(missing_count__lte=2, score__gte=0)

        return final_recipes.order_by('-score')

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