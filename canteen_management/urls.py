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
from inventory.views import inventory_list
from orders.views import checkout
from payments.views import receipt_view
from home.views import (
    index_page, login_page, register_page, logout_view,
    admin_page, admin_update_item, admin_delete_item,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('menu/', inventory_list, name='inventory_list'),
    path('logout/', logout_view, name='logout'),
    path('admin_page/', admin_page, name='admin_page'),
    path('', index_page, name='index_page'),
    path('admin_page/update_item/<int:item_id>/', admin_update_item, name='admin_update_item'),
    path('admin_page/delete_item/<int:item_id>/', admin_delete_item, name='admin_delete_item'),
    path('checkout/', checkout, name='checkout'),
    path('receipt/<int:order_id>/', receipt_view, name='receipt'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
