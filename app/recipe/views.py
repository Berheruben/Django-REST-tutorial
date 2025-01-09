""" """
from django.urls import path
from rest_framework.authentication import TokenAuthentication
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from recipe import serializers
from core.models import Recipe, Tag, Ingredient

app_name = 'recipe'

class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return objects for the current authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        return serializers.RecipeSerializer  # per list, create, update, etc.

    def perform_create(self, serializer):
        """Create a new recipe."""
        serializer.save()

class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,mixins.UpdateModelMixin,mixins.ListModelMixin, viewsets.GenericViewSet):
    """Base viewset for recipe attributes."""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return objects for the current authenticated user only."""
        return self.queryset.filter(user=self.request.user).order_by('-name')

class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()





class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()







