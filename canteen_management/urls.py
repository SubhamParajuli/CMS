"""
URL configuration for canteen_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from canteen_management.media_views import serve_production_media
from inventory.views import inventory_list, inventory_snapshot
from orders.views import checkout
from payments.views import receipt_view
from home.views import (
    index_page, login_page, register_page, logout_view,
    admin_page, admin_sales_analytics, admin_orders_page,
    admin_update_item, admin_delete_item,
    admin_inventory_snapshot, admin_orders_snapshot, admin_sales_analytics_snapshot,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('menu/', inventory_list, name='inventory_list'),
    path('api/inventory/', inventory_snapshot, name='inventory_snapshot'),
    path('logout/', logout_view, name='logout'),
    path('admin_page/', admin_page, name='admin_page'),
    path('admin_page/api/inventory/', admin_inventory_snapshot, name='admin_inventory_snapshot'),
    path('admin_page/analytics/', admin_sales_analytics, name='admin_sales_analytics'),
    path(
        'admin_page/analytics/api/',
        admin_sales_analytics_snapshot,
        name='admin_sales_analytics_snapshot',
    ),
    path('admin_page/orders/', admin_orders_page, name='admin_orders_page'),
    path('admin_page/orders/api/', admin_orders_snapshot, name='admin_orders_snapshot'),
    path('', index_page, name='index_page'),
    path('admin_page/update_item/<int:item_id>/', admin_update_item, name='admin_update_item'),
    path('admin_page/delete_item/<int:item_id>/', admin_delete_item, name='admin_delete_item'),
    path('checkout/', checkout, name='checkout'),
    path('receipt/<int:order_id>/', receipt_view, name='receipt'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
else:
    urlpatterns += [
        path(
            f"{settings.MEDIA_URL.lstrip('/')}<path:path>",
            serve_production_media,
            name='production_media',
        )
    ]
