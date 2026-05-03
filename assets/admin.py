from django.contrib import admin
from .models import (
    Asset, AssetType, Location, Vendor, Purchase, Warranty,
    MaintenanceLog, Config, ConfigAssetHistory, ConfigAssignment,
    Contact, Department, AuditLog,
)

admin.site.register(AssetType)
admin.site.register(Location)
admin.site.register(Vendor)
admin.site.register(Department)
admin.site.register(AuditLog)


class PurchaseInline(admin.StackedInline):
    model = Purchase
    extra = 0


class WarrantyInline(admin.StackedInline):
    model = Warranty
    extra = 0


class MaintenanceLogInline(admin.TabularInline):
    model = MaintenanceLog
    extra = 0


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'asset_type', 'status', 'location', 'serial']
    list_filter = ['status', 'asset_type']
    search_fields = ['make', 'model', 'serial']
    inlines = [PurchaseInline, WarrantyInline, MaintenanceLogInline]


class ConfigAssetHistoryInline(admin.TabularInline):
    model = ConfigAssetHistory
    extra = 0


class ConfigAssignmentInline(admin.TabularInline):
    model = ConfigAssignment
    extra = 0


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'config_type', 'host_config']
    list_filter = ['config_type']
    search_fields = ['name']
    inlines = [ConfigAssetHistoryInline, ConfigAssignmentInline]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'department']
    search_fields = ['name', 'email']
