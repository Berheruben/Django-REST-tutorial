"""tests for recipe APIs."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Recipe, Tag
from recipe.serializers import (RecipeSerializer,RecipeDetailSerializer)

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recipe(user, **params):
    """create and return a new recipe."""
    default = {
        'title': 'Sample Recipe',
        'time_minutes': 10,
        'price': Decimal('5.00'),
        'description': 'Sample Description',
        'link': 'https://sample.com'
    }
    default.update(params)
    recipe = Recipe.objects.create(user=user, **default)
    return recipe


def create_user(**params):
    """create and return a new user."""
    return get_user_model().objects.create_user(**params)

class PublicRecipeApiTests(TestCase):
    """Test the public features of the recipe API."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required."""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test the private features of the recipe API."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.it", password="test124")

        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test that recipes returned are for the authenticated user."""
        user2 = create_user(email='user2@example.com', password='test1234')
        create_recipe(user=user2)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test retrieving a recipe detail."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """test creating a recipe."""
        payload = {
            'title': 'Sample Recipe',
            'time_minutes': 10,
            'price': Decimal('5.00'),

        }
        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key,v in payload.items():
            self.assertEqual(getattr(recipe, key), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link = "https://sample.com/recipe.pdf"
        recipe = create_recipe(user=self.user,title="sample recipe title", link=original_link)
        payload = {
            "title":"Updated Title",
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """test full update of recipe."""
        recipe = create_recipe(user=self.user, title="sample recipe title", link="https://sample.com/recipe.pdf",description="New sample description")
        payload = {
            'title':'Updated Title',
            'time_minutes': 15,
            'price': Decimal('10.00'),
            'link': 'https://sample',
            'description': 'New sample description',
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_errors(self):
        """Test changing the recipe user results in an error."""
        new_user = create_user(email="user2@example.com", password="test124")
        recipe = create_recipe(user=self.user)
        payload = {
            'user': new_user.id
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe."""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test that users cannot delete other users recipes."""
        user2 = create_user(email="user2@example.com,", password="test124")
        recipe = create_recipe(user=user2)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new Tags."""
        payload = {
            "title":"Sample Recipe",
            "time_minutes": 10,
            "price": Decimal('5.00'),
            "tags":[{'name':'Vegan'}, {'name':'Dessert'}]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.tags.count(),2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'],user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing Tags."""
        tag1 = Tag.objects.create(user=self.user, name='Vegan')

        payload = {
            "title":"Sample Recipe",
            "time_minutes": 10,
            "price": Decimal('5.00'),
            "tags":[{'name':'Vegan'}, {'name':'Dessert'}]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe[0]
        self.assertEqual(recipe.tags.count(),2)
        self.assertIn(tag1, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'],user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {'tags':[{'name':'Lunch'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user = self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning and existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name='breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)
        tag_lunch = Tag.objects.create(user=self.user, name='lunch')
        payload = {'tags':[{'name':'lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags."""
        tag = Tag.objects.create(user=self.user, name='dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)
        payload = {'tags':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)














