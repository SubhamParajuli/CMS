from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from inventory.models import Inventory
from orders.models import Order, OrderItem

from .forms import InventoryItemForm, RegistrationForm


# Create your views here.
LOW_STOCK_THRESHOLD = 10
PAGE_SIZE = 12


def _apply_inventory_filters(request):
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

    return {
        'inventory': queryset,
        'page_obj': paginator.get_page(page_number),
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


def _aggregate_total(queryset, field_name):
    return queryset.aggregate(total=Sum(field_name))['total'] or 0


def _format_money(value):
    return f'{value:.2f}'


def _best_selling_items(start_date):
    return list(
        OrderItem.objects.filter(order__is_paid=True, order__order_date__gte=start_date)
        .values('item__item_name', 'item__category')
        .annotate(quantity_sold=Sum('quantity'), order_count=Count('order', distinct=True))
        .order_by('-quantity_sold', 'item__item_name')[:5]
    )


def _serialize_inventory_row(item):
    return {
        'id': item.id,
        'item_name': item.item_name,
        'category': item.category,
        'category_label': item.get_category_display(),
        'price': _format_money(item.price),
        'quantity': item.quantity,
        'is_available': item.is_available,
    }


def _serialize_order_row(order):
    return {
        'id': order.id,
        'username': order.user.username,
        'items': [
            {
                'name': item.item.item_name,
                'quantity': item.quantity,
            }
            for item in order.items.all()
        ],
        'total_amount': _format_money(order.total_amount),
        'is_paid': order.is_paid,
        'order_date_display': timezone.localtime(order.order_date).strftime('%b %d, %Y %I:%M %p'),
    }


def _serialize_top_item(item):
    return {
        'item_name': item['item__item_name'],
        'category': item['item__category'],
        'quantity_sold': item['quantity_sold'],
        'order_count': item['order_count'],
    }


def _serialize_top_customer(customer):
    return {
        'username': customer['user__username'],
        'order_count': customer['order_count'],
        'total_spent': _format_money(customer['total_spent']),
    }


def _serialize_recent_order(order):
    return {
        'id': order.id,
        'username': order.user.username,
        'total_items': order.total_items,
        'total_amount': _format_money(order.total_amount),
        'order_date_display': timezone.localtime(order.order_date).strftime('%b %d, %Y %I:%M %p'),
    }


def _build_admin_sales_analytics_context():
    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)
    month_start = today_start.replace(day=1)

    paid_orders = Order.objects.filter(is_paid=True).select_related('user')
    today_orders = paid_orders.filter(order_date__gte=today_start)
    week_orders = paid_orders.filter(order_date__gte=week_start)
    month_orders = paid_orders.filter(order_date__gte=month_start)
    week_top_items = _best_selling_items(week_start)
    month_top_items = _best_selling_items(month_start)
    top_customers = list(
        month_orders.values('user__username')
        .annotate(order_count=Count('id'), total_spent=Sum('total_amount'))
        .order_by('-total_spent', 'user__username')[:5]
    )
    recent_orders = list(
        paid_orders.prefetch_related('items__item').order_by('-order_date')[:6]
    )

    return {
        'active_admin_page': 'analytics',
        'analytics': {
            'today_order_count': today_orders.count(),
            'today_revenue': _aggregate_total(today_orders, 'total_amount'),
            'week_order_count': week_orders.count(),
            'week_revenue': _aggregate_total(week_orders, 'total_amount'),
            'month_order_count': month_orders.count(),
            'month_revenue': _aggregate_total(month_orders, 'total_amount'),
            'unique_customers': month_orders.values('user_id').distinct().count(),
        },
        'week_top_items': week_top_items,
        'month_top_items': month_top_items,
        'top_week_item': week_top_items[0] if week_top_items else None,
        'top_month_item': month_top_items[0] if month_top_items else None,
        'top_customers': top_customers,
        'recent_orders': recent_orders,
    }


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

    context = {
        **_apply_inventory_filters(request),
        'item_form': item_form,
        'active_admin_page': 'inventory',
    }
       
    return render(request, 'admin.html', context)


@admin_required
def admin_sales_analytics(request):
    return render(request, 'admin_analytics.html', _build_admin_sales_analytics_context())


@admin_required
def admin_sales_analytics_snapshot(request):
    context = _build_admin_sales_analytics_context()

    return JsonResponse(
        {
            'analytics': {
                'today_order_count': context['analytics']['today_order_count'],
                'today_revenue': _format_money(context['analytics']['today_revenue']),
                'week_order_count': context['analytics']['week_order_count'],
                'week_revenue': _format_money(context['analytics']['week_revenue']),
                'month_order_count': context['analytics']['month_order_count'],
                'month_revenue': _format_money(context['analytics']['month_revenue']),
                'unique_customers': context['analytics']['unique_customers'],
            },
            'top_week_item': (
                _serialize_top_item(context['top_week_item']) if context['top_week_item'] else None
            ),
            'top_month_item': (
                _serialize_top_item(context['top_month_item']) if context['top_month_item'] else None
            ),
            'week_top_items': [_serialize_top_item(item) for item in context['week_top_items']],
            'month_top_items': [_serialize_top_item(item) for item in context['month_top_items']],
            'top_customers': [
                _serialize_top_customer(customer) for customer in context['top_customers']
            ],
            'recent_orders': [
                _serialize_recent_order(order) for order in context['recent_orders']
            ],
        }
    )


@admin_required
def admin_orders_page(request):
    timeframe = request.GET.get('range', 'all')
    user_query = (request.GET.get('user') or '').strip()
    orders = Order.objects.select_related('user').prefetch_related('items__item').order_by('-order_date')

    if user_query:
        orders = orders.filter(user__username__icontains=user_query)

    now = timezone.localtime()
    if timeframe == 'week':
        orders = orders.filter(order_date__gte=now - timedelta(days=7))
    elif timeframe == 'month':
        orders = orders.filter(
            order_date__gte=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        )

    paginator = Paginator(orders, 10)

    context = {
        'active_admin_page': 'orders',
        'page_obj': paginator.get_page(request.GET.get('page')),
        'current_range': timeframe,
        'current_user_query': user_query,
        'order_stats': {
            'order_count': orders.count(),
            'paid_count': orders.filter(is_paid=True).count(),
            'revenue': _aggregate_total(orders.filter(is_paid=True), 'total_amount'),
        },
    }

    return render(request, 'admin_orders.html', context)

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
def admin_inventory_snapshot(request):
    inventory_context = _apply_inventory_filters(request)
    page_obj = inventory_context['page_obj']

    return JsonResponse(
        {
            'stats': inventory_context['stats'],
            'items': [_serialize_inventory_row(item) for item in page_obj.object_list],
            'pagination': {
                'page': page_obj.number,
                'pages': page_obj.paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
        }
    )


@admin_required
def admin_orders_snapshot(request):
    timeframe = request.GET.get('range', 'all')
    user_query = (request.GET.get('user') or '').strip()
    orders = Order.objects.select_related('user').prefetch_related('items__item').order_by('-order_date')

    if user_query:
        orders = orders.filter(user__username__icontains=user_query)

    now = timezone.localtime()
    if timeframe == 'week':
        orders = orders.filter(order_date__gte=now - timedelta(days=7))
    elif timeframe == 'month':
        orders = orders.filter(
            order_date__gte=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        )

    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return JsonResponse(
        {
            'stats': {
                'order_count': orders.count(),
                'paid_count': orders.filter(is_paid=True).count(),
                'revenue': str(_aggregate_total(orders.filter(is_paid=True), 'total_amount')),
            },
            'orders': [_serialize_order_row(order) for order in page_obj.object_list],
            'pagination': {
                'page': page_obj.number,
                'pages': page_obj.paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            },
        }
    )



@admin_required
@require_POST
def admin_delete_item(request, item_id):
    item = get_object_or_404(Inventory, id=item_id)
    item.delete()
    messages.info(request, 'Item deleted successfully!')

    return redirect('/admin_page/')
