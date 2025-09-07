"""
URL configuration for dealership_menagment project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
# dealership_menagment/urls.py (or wherever your main urls.py is)

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.shortcuts import redirect
from dealership_app import views
from dealership_app import frontend_views
from dealership_app import admin_views


def admin_redirect(request):
    """Redirect admin to dashboard"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('/dashboard/')
    else:
        return admin_views.custom_admin_login(request)


# Language-independent URLs (admin, AJAX, etc.)
urlpatterns = [
    # Language switching
    path('i18n/', include('django.conf.urls.i18n')),
    
    # AJAX endpoints (no translation needed)
    path('ajax/models/', frontend_views.ajax_models, name='ajax_models'),
    path('ajax/delete-car-image/<int:pk>/', views.ajax_delete_car_image, name="ajax_delete_car_image"),
    path('ajax/reorder-car-images/', views.ajax_reorder_car_images, name="ajax_reorder_car_images"),
    path('ajax/add-equipment/', views.ajax_add_equipment, name="ajax_add_equipment"),
    path('ajax/load-models/', views.ajax_load_models, name='ajax_load_models'),
    path('ajax/update-car-position/', views.ajax_update_car_position, name='ajax_update_car_position'),
    path('ajax/bulk-position-tools/', views.ajax_bulk_position_tools, name='ajax_bulk_position_tools'),
    path('ajax/upload-single-image/', views.ajax_upload_single_image, name='ajax_upload_single_image'),
    path('ajax/check-image-status/<int:image_id>/', views.ajax_check_image_status, name='ajax_check_image_status'),
    
    # Admin URLs (no translation needed)
    path('admin/', admin_redirect, name='admin_redirect'),
    path('admin/login/', admin_views.custom_admin_login, name='admin_login'),
    path('login/', admin_views.custom_admin_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('dashboard/cars/', views.admin_car_list, name="admin_car_list"),
    path('dashboard/cars/add/', views.admin_car_add, name="admin_car_add"),
    path('dashboard/cars/<int:pk>/edit/', views.admin_car_edit, name="admin_car_edit"),
    path('dashboard/cars/<int:pk>/delete/', views.admin_car_delete, name="admin_car_delete"),
    path('dashboard/cars/reorder/', views.admin_car_reorder, name="admin_car_reorder"),
]

# Language-dependent URLs (frontend)
urlpatterns += i18n_patterns(
    path('', frontend_views.index, name='frontend_index'),
    path('vehicles/', frontend_views.vehicle_list, name='frontend_vehicles'),
    path('vehicles/<int:pk>/', frontend_views.vehicle_detail, name='frontend_vehicle_detail'),
    path('about/', frontend_views.about, name='frontend_about'),
    path('contact/', frontend_views.contact, name='frontend_contact'),
    path('terms/', frontend_views.terms, name='frontend_terms'),
    path('privacy/', frontend_views.privacy, name='frontend_privacy'),
)

# Serve static and media files
if settings.DEBUG:
    # In development, serve from STATICFILES_DIRS
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
else:
    # In production, serve from STATIC_ROOT
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
