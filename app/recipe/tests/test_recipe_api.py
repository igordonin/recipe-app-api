from core.models import Recipe
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient

URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    defaults = {
        'title': 'Sample Recipe',
        'time_in_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipesApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@test.com',
            'testPass123'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def retrieve(self):
        Recipe.objects.create(user=self.user, title='My Recipe 1')
        Recipe.objects.create(user=self.user, title='My Recipe 2')

        response = self.client.get(URL)

        recipes = Recipe.objects.all().order_by('-title')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def retrieve_limited_to_user(self):
        another_user = get_user_model().objects.create_user(
            'test2@test.com',
            'testPass123'
        )

        Recipe.objects.create(user=another_user, title='Recipe 1')
        recipe = Recipe.objects.create(user=self.user, title='Recipe 2')

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], recipe.name)

    def test_create_successful(self):
        payload = {
            'title': 'Test Recipe',
            'time_in_minutes': 20,
            'price': 120.00
        }
        self.client.post(URL, payload)

        exists = Recipe.objects.filter(
            user=self.user,
            title=payload['title']
        ).exists()

        self.assertTrue(exists)

    def test_create_invalid(self):
        payload = {'title': ''}
        response = self.client.post(URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
