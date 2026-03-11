from functools import wraps

from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from inventory.models import Inventory
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from .forms import InventoryItemForm, RegistrationForm


# Create your views here.
LOW_STOCK_THRESHOLD = 10
PAGE_SIZE = 12


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url='/login/')
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.is_canteen_admin:
            return view_func(request, *args, **kwargs)

        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('/menu/')

    return _wrapped_view

def index_page(request):
    return render(request, 'index.html')


def login_page(request):
    next_url = request.POST.get('next') or request.GET.get('next') or ''

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            # Admin / Staff redirect
            if user.is_canteen_admin:
                return redirect('/admin_page/')

            # Normal user redirect
            return redirect('/menu/')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html', {'next': next_url})


def register_page(request):
    form = RegistrationForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('/login/')

        messages.error(request, 'Please correct the errors below.')

    return render(request, 'register.html', {'form': form})



@require_POST
@login_required(login_url='/login/')
def logout_view(request):
    user_id = request.user.id if request.user.is_authenticated else None
    logout(request)
    return render(request, 'index.html', {'clear_cart_user_id': user_id})

@admin_required
def admin_page(request):
    if request.method == 'POST':
        item_form = InventoryItemForm(request.POST, request.FILES)
        if item_form.is_valid():
            item_form.save()
            messages.success(request, 'Item added successfully!')
            return redirect('/admin_page/')

        messages.error(request, 'Please correct the item form errors below.')
    else:
        item_form = InventoryItemForm()

    base_queryset = Inventory.objects.all()
    queryset = base_queryset

    current_filter = request.GET.get('filter', 'all')
    if current_filter == 'low_stock':
        queryset = queryset.filter(quantity__lt=LOW_STOCK_THRESHOLD)
    elif current_filter == 'unavailable':
        queryset = queryset.filter(is_available=False)

    sort_map = {
        'name': 'item_name',
        'category': 'category',
        'price': 'price',
        'quantity': 'quantity',
        'status': 'is_available',
    }
    current_sort = request.GET.get('sort', 'name')
    current_dir = request.GET.get('dir', 'asc')
    sort_field = sort_map.get(current_sort, 'item_name')
    if current_dir == 'desc':
        sort_field = f'-{sort_field}'

    queryset = queryset.order_by(sort_field, 'id')

    paginator = Paginator(queryset, PAGE_SIZE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'inventory': queryset,
        'item_form': item_form,
        'page_obj': page_obj,
        'current_filter': current_filter,
        'current_sort': current_sort,
        'current_dir': current_dir,
        'stats': {
            'total_items': base_queryset.count(),
            'available_items': base_queryset.filter(is_available=True).count(),
            'low_stock_items': base_queryset.filter(quantity__lt=LOW_STOCK_THRESHOLD).count(),
        },
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
    }
       
    return render(request, 'admin.html', context)

@admin_required
def admin_update_item(request, item_id):
    item = get_object_or_404(Inventory, id=item_id)
    form = InventoryItemForm(request.POST or None, request.FILES or None, instance=item)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated successfully!')
            return redirect('/admin_page/')

        messages.error(request, 'Please correct the item form errors below.')

    context = {
        'form': form,
        'item': item,
    }
    return render(request, 'update_admin.html', context)



@admin_required
@require_POST
def admin_delete_item(request, item_id):
    item = get_object_or_404(Inventory, id=item_id)
    item.delete()
    messages.info(request, 'Item deleted successfully!')

    return redirect('/admin_page/')
