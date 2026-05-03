from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Assets
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/new/', views.asset_create, name='asset_create'),
    path('assets/import/', views.asset_import, name='asset_import'),
    path('assets/export/', views.asset_export, name='asset_export'),
    path('assets/<uuid:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<uuid:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('assets/<uuid:pk>/retire/', views.asset_retire, name='asset_retire'),
    path('assets/<uuid:pk>/maintenance/add/', views.maintenance_add, name='maintenance_add'),

    # Configs
    path('configs/', views.config_list, name='config_list'),
    path('configs/new/', views.config_create, name='config_create'),
    path('configs/export/', views.config_export, name='config_export'),
    path('configs/<uuid:pk>/', views.config_detail, name='config_detail'),
    path('configs/<uuid:pk>/edit/', views.config_edit, name='config_edit'),
    path('configs/<uuid:pk>/swap/', views.config_swap, name='config_swap'),
    path('configs/<uuid:pk>/assign/', views.config_assign, name='config_assign'),
    path('configs/<uuid:pk>/unassign/', views.config_unassign, name='config_unassign'),

    # Contacts
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/new/', views.contact_create, name='contact_create'),
    path('contacts/<uuid:pk>/', views.contact_detail, name='contact_detail'),
    path('contacts/<uuid:pk>/edit/', views.contact_edit, name='contact_edit'),

    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/new/', views.department_create, name='department_create'),
    path('departments/<uuid:pk>/edit/', views.department_edit, name='department_edit'),

    # Locations
    path('locations/', views.location_list, name='location_list'),
    path('locations/new/', views.location_create, name='location_create'),
    path('locations/<uuid:pk>/edit/', views.location_edit, name='location_edit'),

    # Asset Types
    path('asset-types/', views.asset_type_list, name='asset_type_list'),
    path('asset-types/new/', views.asset_type_create, name='asset_type_create'),
    path('asset-types/<uuid:pk>/edit/', views.asset_type_edit, name='asset_type_edit'),
]
