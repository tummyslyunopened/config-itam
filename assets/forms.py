from django import forms
from .models import (
    Asset, AssetType, Location, Vendor, Purchase, Warranty,
    MaintenanceLog, Config, Contact, Department,
)


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['make', 'model', 'serial', 'asset_type', 'status', 'location', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 3})}


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['vendor', 'cost', 'po_number', 'invoice', 'purchase_date']
        widgets = {'purchase_date': forms.DateInput(attrs={'type': 'date'})}


class WarrantyForm(forms.ModelForm):
    class Meta:
        model = Warranty
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        fields = ['date', 'description', 'performed_by']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ConfigForm(forms.ModelForm):
    class Meta:
        model = Config
        fields = ['name', 'config_type', 'host_config', 'data', 'notes']
        widgets = {
            'data': forms.Textarea(attrs={'rows': 10, 'style': 'font-family:monospace'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['host_config'].queryset = Config.objects.filter(config_type=Config.TYPE_PHYSICAL)
        self.fields['host_config'].required = False


class ConfigSwapForm(forms.Form):
    asset = forms.ModelChoiceField(queryset=Asset.objects.all(), label='New physical asset')


class ConfigAssignForm(forms.Form):
    contact = forms.ModelChoiceField(queryset=Contact.objects.all())


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'department']


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['site', 'room']


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'contact_info', 'support_url']
        widgets = {'contact_info': forms.Textarea(attrs={'rows': 2})}


class AssetTypeForm(forms.ModelForm):
    class Meta:
        model = AssetType
        fields = ['name', 'is_virtual']
