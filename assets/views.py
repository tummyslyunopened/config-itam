import csv
import io
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import (
    Asset, AssetType, Location, Vendor, Purchase, Warranty,
    MaintenanceLog, Config, ConfigAssetHistory, ConfigAssignment,
    Contact, Department,
)
from .forms import (
    AssetForm, PurchaseForm, WarrantyForm, MaintenanceLogForm,
    ConfigForm, ConfigSwapForm, ConfigAssignForm,
    ContactForm, DepartmentForm, LocationForm, VendorForm, AssetTypeForm,
)


# ── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    ctx = {
        'asset_count': Asset.objects.count(),
        'config_count': Config.objects.count(),
        'contact_count': Contact.objects.count(),
        'active_count': Asset.objects.filter(status=Asset.STATUS_ACTIVE).count(),
        'recent_assets': Asset.objects.order_by('-created_at')[:5],
        'recent_configs': Config.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard.html', ctx)


# ── Assets ────────────────────────────────────────────────────────────────────

@login_required
def asset_list(request):
    qs = Asset.objects.select_related('asset_type', 'location')
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    type_id = request.GET.get('type', '')
    location_id = request.GET.get('location', '')
    if q:
        qs = qs.filter(Q(make__icontains=q) | Q(model__icontains=q) | Q(serial__icontains=q) | Q(notes__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if type_id:
        qs = qs.filter(asset_type_id=type_id)
    if location_id:
        qs = qs.filter(location_id=location_id)
    ctx = {
        'assets': qs,
        'asset_types': AssetType.objects.all(),
        'locations': Location.objects.all(),
        'status_choices': Asset.STATUS_CHOICES,
        'q': q, 'status': status, 'type_id': type_id, 'location_id': location_id,
    }
    return render(request, 'assets/list.html', ctx)


@login_required
def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    ctx = {
        'asset': asset,
        'purchase': getattr(asset, 'purchase', None),
        'warranty': getattr(asset, 'warranty', None),
        'maintenance_logs': asset.maintenance_logs.all(),
        'configs': asset.configs.select_related('config').all(),
    }
    return render(request, 'assets/detail.html', ctx)


@login_required
def asset_create(request):
    form = AssetForm(request.POST or None)
    purchase_form = PurchaseForm(request.POST or None)
    warranty_form = WarrantyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        asset = form.save()
        if any(purchase_form.data.get(f) for f in ['vendor', 'cost', 'po_number', 'invoice', 'purchase_date']):
            if purchase_form.is_valid():
                p = purchase_form.save(commit=False)
                p.asset = asset
                p.save()
        if warranty_form.data.get('end_date'):
            if warranty_form.is_valid():
                w = warranty_form.save(commit=False)
                w.asset = asset
                w.save()
        config = Config.objects.create()
        ConfigAssetHistory.objects.create(config=config, asset=asset)
        messages.success(request, 'Asset created.')
        return redirect('asset_detail', pk=asset.pk)
    return render(request, 'assets/form.html', {'form': form, 'purchase_form': purchase_form, 'warranty_form': warranty_form, 'title': 'Add Asset'})


@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    form = AssetForm(request.POST or None, instance=asset)
    purchase_form = PurchaseForm(request.POST or None, instance=getattr(asset, 'purchase', None))
    warranty_form = WarrantyForm(request.POST or None, instance=getattr(asset, 'warranty', None))
    if request.method == 'POST' and form.is_valid():
        form.save()
        if purchase_form.is_valid():
            p = purchase_form.save(commit=False)
            p.asset = asset
            p.save()
        if warranty_form.is_valid():
            w = warranty_form.save(commit=False)
            w.asset = asset
            w.save()
        messages.success(request, 'Asset updated.')
        return redirect('asset_detail', pk=asset.pk)
    return render(request, 'assets/form.html', {'form': form, 'purchase_form': purchase_form, 'warranty_form': warranty_form, 'title': 'Edit Asset', 'asset': asset})


@login_required
def asset_retire(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', 'retired')
        asset.status = action
        asset.save()
        messages.success(request, f'Asset marked as {asset.get_status_display()}.')
        return redirect('asset_detail', pk=asset.pk)
    return render(request, 'assets/retire.html', {'asset': asset})


@login_required
def maintenance_add(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    form = MaintenanceLogForm(request.POST or None, initial={'date': timezone.now().date()})
    if request.method == 'POST' and form.is_valid():
        log = form.save(commit=False)
        log.asset = asset
        log.save()
        messages.success(request, 'Maintenance log entry added.')
        return redirect('asset_detail', pk=asset.pk)
    return render(request, 'assets/maintenance_form.html', {'form': form, 'asset': asset})


# ── Configs ───────────────────────────────────────────────────────────────────

@login_required
def config_list(request):
    qs = Config.objects.select_related('host_config')
    q = request.GET.get('q', '')
    config_type = request.GET.get('type', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(notes__icontains=q))
    if config_type:
        qs = qs.filter(config_type=config_type)
    ctx = {'configs': qs, 'q': q, 'config_type': config_type, 'type_choices': Config.TYPE_CHOICES}
    return render(request, 'configs/list.html', ctx)


@login_required
def config_detail(request, pk):
    config = get_object_or_404(Config, pk=pk)
    ctx = {
        'config': config,
        'current_asset': config.current_asset,
        'current_contact': config.current_contact,
        'asset_history': config.asset_history.select_related('asset').all(),
        'assignments': config.assignments.select_related('contact').all(),
        'vm_configs': config.vm_configs.all(),
    }
    return render(request, 'configs/detail.html', ctx)


@login_required
def config_create(request):
    form = ConfigForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        config = form.save()
        messages.success(request, 'Config created.')
        return redirect('config_detail', pk=config.pk)
    return render(request, 'configs/form.html', {'form': form, 'title': 'Add Config'})


@login_required
def config_edit(request, pk):
    config = get_object_or_404(Config, pk=pk)
    form = ConfigForm(request.POST or None, instance=config)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Config updated.')
        return redirect('config_detail', pk=config.pk)
    return render(request, 'configs/form.html', {'form': form, 'title': 'Edit Config', 'config': config})


@login_required
def config_swap(request, pk):
    """Reassign a config to a different physical asset."""
    config = get_object_or_404(Config, pk=pk)
    form = ConfigSwapForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_asset = form.cleaned_data['asset']
        today = timezone.now().date()
        config.asset_history.filter(removed_date__isnull=True).update(removed_date=today)
        ConfigAssetHistory.objects.create(config=config, asset=new_asset, assigned_date=today)
        messages.success(request, f'Config swapped to {new_asset}.')
        return redirect('config_detail', pk=config.pk)
    ctx = {'config': config, 'form': form, 'current_asset': config.current_asset}
    return render(request, 'configs/swap.html', ctx)


@login_required
def config_assign(request, pk):
    """Assign a contact to a config."""
    config = get_object_or_404(Config, pk=pk)
    form = ConfigAssignForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        today = timezone.now().date()
        config.assignments.filter(returned_date__isnull=True).update(returned_date=today)
        ConfigAssignment.objects.create(config=config, contact=form.cleaned_data['contact'], assigned_date=today)
        messages.success(request, 'Contact assigned.')
        return redirect('config_detail', pk=config.pk)
    return render(request, 'configs/assign.html', {'config': config, 'form': form})


@login_required
def config_unassign(request, pk):
    """End the current contact assignment."""
    config = get_object_or_404(Config, pk=pk)
    if request.method == 'POST':
        config.assignments.filter(returned_date__isnull=True).update(returned_date=timezone.now().date())
        messages.success(request, 'Contact unassigned.')
    return redirect('config_detail', pk=config.pk)


# ── Contacts ──────────────────────────────────────────────────────────────────

@login_required
def contact_list(request):
    qs = Contact.objects.select_related('department')
    q = request.GET.get('q', '')
    dept_id = request.GET.get('dept', '')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q))
    if dept_id:
        qs = qs.filter(department_id=dept_id)
    ctx = {'contacts': qs, 'departments': Department.objects.all(), 'q': q, 'dept_id': dept_id}
    return render(request, 'contacts/list.html', ctx)


@login_required
def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    ctx = {
        'contact': contact,
        'assignments': contact.config_assignments.select_related('config').all(),
    }
    return render(request, 'contacts/detail.html', ctx)


@login_required
def contact_create(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        contact = form.save()
        messages.success(request, 'Contact created.')
        return redirect('contact_detail', pk=contact.pk)
    return render(request, 'contacts/form.html', {'form': form, 'title': 'Add Contact'})


@login_required
def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    form = ContactForm(request.POST or None, instance=contact)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Contact updated.')
        return redirect('contact_detail', pk=contact.pk)
    return render(request, 'contacts/form.html', {'form': form, 'title': 'Edit Contact', 'contact': contact})


# ── Departments ───────────────────────────────────────────────────────────────

@login_required
def department_list(request):
    return render(request, 'departments/list.html', {'departments': Department.objects.all()})


@login_required
def department_create(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Department created.')
        return redirect('department_list')
    return render(request, 'departments/form.html', {'form': form, 'title': 'Add Department'})


@login_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Department updated.')
        return redirect('department_list')
    return render(request, 'departments/form.html', {'form': form, 'title': 'Edit Department', 'dept': dept})


# ── CSV import / export ───────────────────────────────────────────────────────

@login_required
def asset_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assets.csv"'
    writer = csv.writer(response)
    writer.writerow(['make', 'model', 'serial', 'type', 'status', 'location', 'notes'])
    for a in Asset.objects.select_related('asset_type', 'location'):
        writer.writerow([a.make, a.model, a.serial, a.asset_type or '', a.status, a.location or '', a.notes])
    return response


@login_required
def asset_import(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        f = io.TextIOWrapper(request.FILES['csv_file'], encoding='utf-8')
        reader = csv.DictReader(f)
        created = 0
        for row in reader:
            asset_type = None
            if row.get('type'):
                asset_type, _ = AssetType.objects.get_or_create(name=row['type'].strip())
            location = None
            if row.get('location'):
                location, _ = Location.objects.get_or_create(site=row['location'].strip())
            Asset.objects.create(
                make=row.get('make', '').strip(),
                model=row.get('model', '').strip(),
                serial=row.get('serial', '').strip(),
                asset_type=asset_type,
                status=row.get('status', Asset.STATUS_ACTIVE).strip(),
                location=location,
                notes=row.get('notes', '').strip(),
            )
            created += 1
        messages.success(request, f'Imported {created} assets.')
        return redirect('asset_list')
    return render(request, 'assets/import.html')


# ── Locations ─────────────────────────────────────────────────────────────────

@login_required
def location_list(request):
    return render(request, 'locations/list.html', {'locations': Location.objects.all()})


@login_required
def location_create(request):
    form = LocationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Location created.')
        return redirect('location_list')
    return render(request, 'locations/form.html', {'form': form, 'title': 'Add Location'})


@login_required
def location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk)
    form = LocationForm(request.POST or None, instance=location)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Location updated.')
        return redirect('location_list')
    return render(request, 'locations/form.html', {'form': form, 'title': 'Edit Location', 'location': location})


# ── Asset Types ───────────────────────────────────────────────────────────────

@login_required
def asset_type_list(request):
    return render(request, 'asset_types/list.html', {'asset_types': AssetType.objects.all()})


@login_required
def asset_type_create(request):
    form = AssetTypeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Asset type created.')
        return redirect('asset_type_list')
    return render(request, 'asset_types/form.html', {'form': form, 'title': 'Add Asset Type'})


@login_required
def asset_type_edit(request, pk):
    asset_type = get_object_or_404(AssetType, pk=pk)
    form = AssetTypeForm(request.POST or None, instance=asset_type)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Asset type updated.')
        return redirect('asset_type_list')
    return render(request, 'asset_types/form.html', {'form': form, 'title': 'Edit Asset Type', 'asset_type': asset_type})


# ── CSV import / export ───────────────────────────────────────────────────────

@login_required
def config_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="configs.csv"'
    writer = csv.writer(response)
    writer.writerow(['name', 'type', 'host_config', 'effective_serial', 'notes'])
    for c in Config.objects.select_related('host_config'):
        writer.writerow([str(c), c.config_type, str(c.host_config) if c.host_config else '', c.effective_serial or '', c.notes])
    return response
