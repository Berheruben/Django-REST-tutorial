""" """
from django.urls import path
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

from rest_framework.authentication import TokenAuthentication
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from recipe import serializers
from core.models import Recipe, Tag, Ingredient
from rest_framework.response import Response
from rest_framework.decorators import action
app_name = 'recipe'

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name='tags',
                type=OpenApiTypes.STR,
                description='Comma separates list of IDs to filter',),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separates list of ingredients IDs to filter',
            )
        ]
    )
)

class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _params_to_ints(self, qs):
        """Convert a list of string IDs to a list of integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Return objects for the current authenticated user only."""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')

        # parti dai recipe dell'utente
        queryset = self.queryset.filter(user=self.request.user)

        # se 'tags' è presente, filtra
        if tags:
            tag_ids = self._params_to_ints(tags)  # converte '1,2,3' in [1, 2, 3]
            queryset = queryset.filter(tags__id__in=tag_ids)

        # se 'ingredients' è presente, filtra
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        # ordina come ti serve (per es. -id) in modo da corrispondere ai test
        return queryset.order_by('-id')


    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return serializers.RecipeSerializer  # per list, create, update, etc.


    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save()

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe."""
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name='assigned_only',
                type=OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipe',
            )
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,mixins.UpdateModelMixin,mixins.ListModelMixin, viewsets.GenericViewSet):
    """Base viewset for recipe attributes."""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return objects for the current authenticated user only."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset

        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False).distinct()

        return queryset.filter(user=self.request.user).order_by('-name')

class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()





class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()







