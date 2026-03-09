from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class InventoryAuthRedirectTests(TestCase):
    def test_inventory_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse('inventory_list'))

        self.assertRedirects(response, '/login/?next=/menu/')
