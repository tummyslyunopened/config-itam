import uuid
from django.db import models
from django.utils import timezone


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name='contacts')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    contact_info = models.TextField(blank=True)
    support_url = models.URLField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.CharField(max_length=100)
    room = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['site', 'room']

    def __str__(self):
        return f'{self.site} / {self.room}' if self.room else self.site


class AssetType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    is_virtual = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Asset(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_SPARE = 'spare'
    STATUS_REPAIR = 'in-repair'
    STATUS_RETIRED = 'retired'
    STATUS_DISPOSED = 'disposed'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SPARE, 'Spare'),
        (STATUS_REPAIR, 'In Repair'),
        (STATUS_RETIRED, 'Retired'),
        (STATUS_DISPOSED, 'Disposed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial = models.CharField(max_length=200, blank=True, help_text='Leave blank for virtual machine assets')
    asset_type = models.ForeignKey(AssetType, null=True, blank=True, on_delete=models.SET_NULL, related_name='assets')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL, related_name='assets')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['make', 'model']

    def __str__(self):
        parts = [p for p in [self.make, self.model, self.serial] if p]
        return ' '.join(parts) if parts else f'Asset {str(self.id)[:8]}'

    @property
    def effective_serial(self):
        entry = self.configs.filter(config__config_type=Config.TYPE_VIRTUAL).select_related('config').first()
        if entry:
            return entry.config.effective_serial
        return self.serial


class Purchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='purchase')
    vendor = models.ForeignKey(Vendor, null=True, blank=True, on_delete=models.SET_NULL)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    po_number = models.CharField(max_length=100, blank=True)
    invoice = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'Purchase for {self.asset}'


class Warranty(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='warranty')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'warranties'

    def __str__(self):
        return f'Warranty for {self.asset}'

    @property
    def is_expired(self):
        return self.end_date and self.end_date < timezone.now().date()


class MaintenanceLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_logs')
    date = models.DateField()
    description = models.TextField()
    performed_by = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.date} — {self.asset}'


class Config(models.Model):
    TYPE_PHYSICAL = 'physical'
    TYPE_VIRTUAL = 'virtual'
    TYPE_CHOICES = [
        (TYPE_PHYSICAL, 'Physical'),
        (TYPE_VIRTUAL, 'Virtual Machine'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=253, blank=True, help_text='Optional label')
    config_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_PHYSICAL)
    host_config = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='vm_configs',
        help_text='For VM configs: the host hypervisor config'
    )
    data = models.JSONField(default=dict, blank=True, help_text='Arbitrary configuration data — schema not enforced')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name', 'id']

    def __str__(self):
        return self.name if self.name else f'Config {str(self.id)[:8]}'

    @property
    def current_asset(self):
        history = self.asset_history.filter(removed_date__isnull=True).first()
        return history.asset if history else None

    @property
    def current_contact(self):
        assignment = self.assignments.filter(returned_date__isnull=True).first()
        return assignment.contact if assignment else None

    @property
    def effective_serial(self):
        if self.config_type == self.TYPE_PHYSICAL:
            asset = self.current_asset
            return asset.serial if asset else None
        host = self.host_config
        while host is not None:
            if host.config_type == self.TYPE_PHYSICAL:
                asset = host.current_asset
                return asset.serial if asset else None
            host = host.host_config
        return None


class ConfigAssetHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(Config, on_delete=models.CASCADE, related_name='asset_history')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='configs')
    assigned_date = models.DateField(default=timezone.now)
    removed_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_date']

    def __str__(self):
        return f'{self.config} → {self.asset} ({self.assigned_date})'


class ConfigAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(Config, on_delete=models.CASCADE, related_name='assignments')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='config_assignments')
    assigned_date = models.DateField(default=timezone.now)
    returned_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-assigned_date']

    def __str__(self):
        return f'{self.config} → {self.contact}'

    @property
    def is_active(self):
        return self.returned_date is None


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_name = models.CharField(max_length=100)
    object_id = models.UUIDField()
    field = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f'{self.model_name} {self.field} @ {self.changed_at:%Y-%m-%d %H:%M}'
