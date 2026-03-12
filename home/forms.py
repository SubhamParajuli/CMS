from decimal import Decimal
from pathlib import Path

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

from accounts.models import CustomUser
from inventory.models import Inventory


ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
ALLOWED_IMAGE_CONTENT_TYPES = {
    'image/gif',
    'image/jpeg',
    'image/png',
    'image/webp',
}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


class AdminImageInput(forms.ClearableFileInput):
    template_name = 'widgets/admin_image_input.html'
    initial_text = 'Current file'
    input_text = 'Choose replacement image'
    clear_checkbox_label = 'Remove current image'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['display_name'] = Path(value.name).name if value else ''
        return context


class RegistrationForm(forms.Form):
    role = forms.ChoiceField(
        choices=[
            (value, label)
            for value, label in CustomUser.ROLE_CHOICES
            if value in CustomUser.registration_roles()
        ],
        error_messages={'invalid_choice': 'Invalid role selected'},
        widget=forms.Select(attrs={'class': 'form-select mb-2'}),
    )
    user_code = forms.CharField(
        max_length=5,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control mb-2',
                'inputmode': 'numeric',
                'maxlength': '5',
            }
        ),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control mb-2'}),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-2', 'id': 'id_password'}),
    )
    password_confirm = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control mb-2', 'id': 'id_password_confirm'}),
        label='Confirm Password',
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned_data

    def clean_user_code(self):
        user_code = (self.cleaned_data.get('user_code') or '').strip()

        if not CustomUser.is_valid_user_code(user_code):
            raise ValidationError('UserCode must be exactly 5 numeric characters')

        if CustomUser.objects.filter(user_code=user_code).exists():
            raise ValidationError('UserCode already exists')

        return user_code

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()

        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('Username already exists')

        return username

    def clean_role(self):
        role = (self.cleaned_data.get('role') or '').strip()

        if role not in CustomUser.registration_roles():
            raise ValidationError('Invalid role selected')

        return role

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def save(self):
        return CustomUser.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            role=self.cleaned_data['role'],
            user_code=self.cleaned_data['user_code'],
        )


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['item_name', 'category', 'price', 'quantity', 'food_image', 'is_available']
        widgets = {
            'item_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. Chicken Burger',
                }
            ),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '1',
                    'min': '1',
                    'inputmode': 'numeric',
                    'placeholder': '0',
                }
            ),
            'quantity': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'inputmode': 'numeric',
                    'placeholder': '0',
                }
            ),
            'food_image': AdminImageInput(
                attrs={
                    'class': 'admin-image-widget__native-input',
                    'accept': 'image/*',
                }
            ),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_item_name(self):
        item_name = ' '.join((self.cleaned_data.get('item_name') or '').split())
        if not item_name:
            raise ValidationError('Item name is required.')
        if len(item_name) < 2:
            raise ValidationError('Item name must be at least 2 characters long.')
        duplicate_exists = Inventory.objects.exclude(pk=self.instance.pk).filter(
            item_name__iexact=item_name
        ).exists()
        if duplicate_exists:
            raise ValidationError('An item with this name already exists.')
        return item_name

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None:
            return price
        if price <= 0:
            raise ValidationError('Price must be at least Rs 1.')
        if price != price.quantize(Decimal('1')):
            raise ValidationError('Price must be a whole rupee amount.')
        return price

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise ValidationError('Quantity cannot be negative.')
        return quantity

    def clean_food_image(self):
        food_image = self.cleaned_data.get('food_image')
        if not food_image:
            return food_image

        extension = Path(food_image.name).suffix.lower()
        content_type = getattr(food_image, 'content_type', '')

        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError('Upload a JPG, PNG, WEBP, or GIF image.')

        # if not content_type or content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        #     raise ValidationError('Upload a valid image file.')

        if food_image.size > MAX_IMAGE_SIZE:
            raise ValidationError('Image size must be 5 MB or smaller.')

        current_position = food_image.tell() if hasattr(food_image, 'tell') else None
        # try:
        #     Image.open(food_image).verify()
        # except (UnidentifiedImageError, OSError, ValueError):
        #     raise ValidationError('Upload a valid image file.')
        # finally:
        #     if hasattr(food_image, 'seek'):
        #         food_image.seek(current_position or 0)

        return food_image

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        is_available = cleaned_data.get('is_available')

        if quantity is not None and quantity <= 0 and is_available:
            cleaned_data['is_available'] = False

        return cleaned_data
