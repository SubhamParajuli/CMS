from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from inventory.models import Inventory


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class AdminAccessControlTests(TestCase):
    def setUp(self):
        self.student = CustomUser.objects.create_user(
            username='student_user',
            password='testpass123',
            user_code='12345',
            role='student',
        )
        self.admin_user = CustomUser.objects.create_user(
            username='admin_user',
            password='testpass123',
            user_code='54321',
            role='admin',
            is_staff=True,
        )
        self.item = Inventory.objects.create(
            item_name='Tea',
            category='beverages',
            price='25.00',
            quantity=10,
        )

    def test_admin_page_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse('admin_page'))

        self.assertRedirects(response, '/login/?next=/admin_page/')

    def test_student_cannot_access_admin_page(self):
        self.client.login(username='student_user', password='testpass123')

        response = self.client.get(reverse('admin_page'))

        self.assertRedirects(response, '/menu/')

    def test_student_cannot_access_update_page(self):
        self.client.login(username='student_user', password='testpass123')

        response = self.client.get(reverse('admin_update_item', args=[self.item.id]))

        self.assertRedirects(response, '/menu/')

    def test_student_cannot_delete_item(self):
        self.client.login(username='student_user', password='testpass123')

        response = self.client.post(reverse('admin_delete_item', args=[self.item.id]))

        self.assertRedirects(response, '/menu/')
        self.assertTrue(Inventory.objects.filter(id=self.item.id).exists())

    def test_admin_can_access_admin_routes(self):
        self.client.login(username='admin_user', password='testpass123')

        dashboard_response = self.client.get(reverse('admin_page'))
        update_response = self.client.get(reverse('admin_update_item', args=[self.item.id]))

        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(update_response.status_code, 200)

    def test_admin_delete_requires_post(self):
        self.client.login(username='admin_user', password='testpass123')

        response = self.client.get(reverse('admin_delete_item', args=[self.item.id]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Inventory.objects.filter(id=self.item.id).exists())

    def test_admin_can_delete_item_with_post(self):
        self.client.login(username='admin_user', password='testpass123')

        response = self.client.post(reverse('admin_delete_item', args=[self.item.id]))

        self.assertRedirects(response, reverse('admin_page'))
        self.assertFalse(Inventory.objects.filter(id=self.item.id).exists())
