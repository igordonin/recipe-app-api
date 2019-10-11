from core.models import Ingredient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from recipe.serializers import IngredientSerializer
from rest_framework import status
from rest_framework.test import APIClient

URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@test.com',
            'testPass123'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def retrieve(self):
        Ingredient.objects.create(user=self.user, name='Cucumber')
        Ingredient.objects.create(user=self.user, name='Basil')

        response = self.client.get(URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def retrieve_limited_to_user(self):
        another_user = get_user_model().objects.create_user(
            'test2@test.com',
            'testPass123'
        )

        Ingredient.objects.create(user=another_user, name='Cucumber')
        ingredient = Ingredient.objects.create(user=self.user, name='Basil')

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], ingredient.name)

    def test_create_successful(self):
        payload = {'name': 'Test Ingredient'}
        self.client.post(URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_invalid(self):
        payload = {'name': ''}
        response = self.client.post(URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
