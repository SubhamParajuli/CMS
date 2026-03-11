from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from inventory.models import Inventory


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class InventoryAuthRedirectTests(TestCase):
    def test_inventory_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse('inventory_list'))

        self.assertRedirects(response, '/login/?next=/menu/')


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class InventoryImageRenderingTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='menu_user',
            password='testpass123',
            user_code='55555',
            role='student',
        )
        self.client.login(username='menu_user', password='testpass123')

    def test_media_root_is_separate_from_static_files(self):
        self.assertNotEqual(str(settings.MEDIA_ROOT), str(settings.STATICFILES_DIRS[0]))

    def test_menu_uses_media_url_for_uploaded_image(self):
        Inventory.objects.create(
            item_name='Tea',
            category='beverages',
            price='25.00',
            quantity=10,
            food_image='inventory_images/test-image.jpg',
            is_available=True,
        )

        response = self.client.get(reverse('inventory_list'))

        self.assertContains(response, '/media/inventory_images/test-image.jpg')
        self.assertContains(response, 'data-fallback-src="/static/inventory_images/momo.webp"')

    def test_menu_uses_static_fallback_for_missing_image(self):
        Inventory.objects.create(
            item_name='Plain Rice',
            category='main_course',
            price='90.00',
            quantity=5,
            is_available=True,
        )

        response = self.client.get(reverse('inventory_list'))

        self.assertContains(response, '/static/inventory_images/momo.webp')

    def test_menu_script_renders_cart_without_innerhtml_templates(self):
        Inventory.objects.create(
            item_name='Safe Item',
            category='snacks',
            price='30.00',
            quantity=2,
            is_available=True,
        )

        response = self.client.get(reverse('inventory_list'))

        self.assertContains(response, 'container.replaceChildren()')
        self.assertNotContains(response, 'container.innerHTML +=')

    def test_menu_uses_stacked_mobile_layout(self):
        Inventory.objects.create(
            item_name='Mobile Item',
            category='snacks',
            price='40.00',
            quantity=3,
            is_available=True,
        )

        response = self.client.get(reverse('inventory_list'))

        self.assertContains(response, 'menu-layout d-flex flex-column flex-lg-row')
        self.assertContains(response, 'menu-panel flex-grow-1 p-3 order-2 order-lg-1')
        self.assertContains(response, 'cart-sidebar shadow-lg d-flex flex-column order-1 order-lg-2')
        self.assertContains(response, '@media (max-width: 991.98px)')
