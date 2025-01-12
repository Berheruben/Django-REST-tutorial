"""Tests for the ingredients API."""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Return ingredient detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email="user@example.com",password="test123"):
    """create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients API."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients."""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the authorized user ingredients API."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving ingredients."""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that ingredients returned are for the authenticated user."""
        user2 = create_user(email="user2@example.com", password="test123")
        ingredient = Ingredient.objects.create(user=user2, name='Vinegar')

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Vinegar')
        url = detail_url(ingredient.id)
        payload = {'name': 'Cabbage'}
        self.client.patch(url, payload)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Vinegar')
        url = detail_url(ingredient.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Apples')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Turkey')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Apple crumble',
            time_minutes=5,
            price=Decimal('10.00')
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(
            INGREDIENTS_URL,
            {'assigned_only': 1}
        )

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test that filtered ingredients are unique."""
        ingredient = Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Cheese')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Egg benedict',
            time_minutes=30,
            price=Decimal('12.00')
        )
        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Coriander eggs on toast',
            time_minutes=20,
            price=Decimal('5.00')
        )
        recipe2.ingredients.add(ingredient)

        res = self.client.get(
            INGREDIENTS_URL,
            {'assigned_only': 1}
        )

        self.assertEqual(len(res.data), 1)



