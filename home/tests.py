from django.core.files.uploadedfile import SimpleUploadedFile
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

    def test_admin_page_get_does_not_show_success_message(self):
        self.client.login(username='admin_user', password='testpass123')

        response = self.client.get(reverse('admin_page'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Item added successfully!')

    def test_admin_page_shows_real_inventory_stats(self):
        Inventory.objects.create(
            item_name='Burger',
            category='snacks',
            price='150.00',
            quantity=3,
            is_available=True,
        )
        Inventory.objects.create(
            item_name='Coffee',
            category='beverages',
            price='60.00',
            quantity=6,
            is_available=False,
        )
        self.client.login(username='admin_user', password='testpass123')

        response = self.client.get(reverse('admin_page'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats']['total_items'], 3)
        self.assertEqual(response.context['stats']['available_items'], 2)
        self.assertEqual(response.context['stats']['low_stock_items'], 2)

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


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class RegistrationTests(TestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.existing_user = CustomUser.objects.create_user(
            username='existing_user',
            password='testpass123',
            user_code='11111',
            role='student',
        )

    def test_registration_rejects_duplicate_user_code(self):
        response = self.client.post(
            self.register_url,
            {
                'username': 'new_user',
                'password': 'testpass123',
                'user_code': '11111',
                'role': 'student',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'UserCode already exists')
        self.assertEqual(CustomUser.objects.filter(username='new_user').count(), 0)

    def test_registration_rejects_invalid_role(self):
        response = self.client.post(
            self.register_url,
            {
                'username': 'fake_admin',
                'password': 'testpass123',
                'user_code': '22222',
                'role': 'admin',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid role selected')
        self.assertFalse(CustomUser.objects.filter(username='fake_admin').exists())

    def test_registration_creates_non_admin_user(self):
        response = self.client.post(
            self.register_url,
            {
                'username': 'teacher_user',
                'password': 'testpass123',
                'password_confirm': 'testpass123',
                'user_code': '33333',
                'role': 'teacher',
            },
        )

        self.assertRedirects(response, reverse('login'))

        user = CustomUser.objects.get(username='teacher_user')
        self.assertEqual(user.role, 'teacher')
        self.assertFalse(user.is_staff)


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class LegacyAdminLoginTests(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin',
            password='admin',
            user_code='99999',
        )
        CustomUser.objects.filter(pk=self.admin_user.pk).update(user_code='')

    def test_legacy_admin_can_log_in_through_app_login(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'admin',
                'password': 'admin',
            },
        )

        self.assertRedirects(response, reverse('admin_page'))

    def test_legacy_admin_can_log_in_through_django_admin_login(self):
        response = self.client.post(
            reverse('admin:login'),
            {
                'username': 'admin',
                'password': 'admin',
                'next': reverse('admin:index'),
            },
        )

        self.assertRedirects(response, reverse('admin:index'))


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class InventoryFormValidationTests(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            username='inventory_admin',
            password='testpass123',
            user_code='44444',
            role='admin',
        )
        self.client.login(username='inventory_admin', password='testpass123')
        self.item = Inventory.objects.create(
            item_name='Momo',
            category='snacks',
            price='120.00',
            quantity=10,
            is_available=True,
        )

    def test_admin_page_rejects_negative_price(self):
        response = self.client.post(
            reverse('admin_page'),
            {
                'item_name': 'Bad Item',
                'category': 'snacks',
                'price': '-10.00',
                'quantity': '5',
                'is_available': 'on',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Price cannot be negative.')
        self.assertFalse(Inventory.objects.filter(item_name='Bad Item').exists())

    def test_admin_update_rejects_invalid_image_upload(self):
        invalid_file = SimpleUploadedFile(
            'not-an-image.txt',
            b'plain text content',
            content_type='text/plain',
        )

        response = self.client.post(
            reverse('admin_update_item', args=[self.item.id]),
            {
                'item_name': 'Momo',
                'category': 'snacks',
                'price': '120.00',
                'quantity': '10',
                'is_available': 'on',
                'food_image': invalid_file,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upload a valid image')

        self.item.refresh_from_db()
        self.assertEqual(self.item.item_name, 'Momo')
        self.assertFalse(bool(self.item.food_image))

    def test_admin_page_create_respects_unchecked_is_available(self):
        response = self.client.post(
            reverse('admin_page'),
            {
                'item_name': 'Hidden Item',
                'category': 'other',
                'price': '50.00',
                'quantity': '4',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('admin_page'))
        self.assertContains(response, 'Item added successfully!')

        item = Inventory.objects.get(item_name='Hidden Item')
        self.assertFalse(item.is_available)
