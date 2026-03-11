from django.test import TestCase

from .models import CustomUser


class CustomUserModelTests(TestCase):
    def test_create_superuser_defaults_to_admin_role(self):
        user = CustomUser.objects.create_superuser(
            username='root_user',
            password='testpass123',
            user_code='99999',
        )

        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_admin_role_is_treated_as_canteen_admin(self):
        user = CustomUser.objects.create_user(
            username='admin_role_user',
            password='testpass123',
            user_code='88888',
            role='admin',
        )

        self.assertTrue(user.is_canteen_admin)
        self.assertTrue(user.is_staff)
