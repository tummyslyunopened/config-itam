# config-itam

IT Asset Management system — SQLite DB with Django WebUI for tracking hardware assets across an organization.

Single application user (Django's built-in auth). Each asset has a contact person who does not need to be an app user.

Configuration is decoupled from physical hardware — a `Config` record represents a logical machine identity (hostname, OS, role, network config, etc.) and can be reassigned to a new physical `Asset` when hardware is replaced.

Virtual machines are tracked as assets whose serial number is derived through their config relationship to a host, not stored directly.

---

## Features

### Asset Inventory
- Register physical machines (desktops, laptops, servers, peripherals)
- Register virtual machine assets (no physical serial of their own)
- Track make, model, serial number, and purchase date for physical assets
- Track physical location (site, room)
- Asset status: active, spare, in-repair, retired, disposed

### Configuration Management
- `Config` represents the logical identity of a machine, independent of hardware
- Tracks hostname, OS, OS version, IP address, role/function, domain, and notes
- A `Config` can be linked to an `Asset` (the current physical device carrying it)
- When hardware is replaced, reassign the `Config` to the new `Asset` — history preserved
- Full history of which physical asset held each config over time
- Assign a contact to a `Config` (not the physical asset)

### Virtual Machine Tracking
- A `Config` can be designated as a VM config, with a FK to a host `Config`
- A VM asset's effective serial number is derived via:
  `VM Asset → VM Config → host Config → current physical Asset → serial`
- The serial is never stored on the VM asset directly — it is always read through the chain
- When a host config is swapped to a new physical asset (new serial), all VM configs and their assets automatically reflect the new serial through the relationship — no explicit update required
- VM configs can be listed under their host config in the UI

### Asset Lifecycle
- Record purchase info (vendor, cost, PO number, invoice)
- Warranty start/end dates
- Maintenance log per asset (date, description, performed by)
- Retirement and disposal workflow with audit trail

### User & Department Management
- Contact directory (name, email, phone, department)
- Department list for grouping contacts and configs

### Search & Reporting
- Search and filter assets by status, type, location
- Search and filter configs by hostname, OS, role, contact, department, host
- Dashboard with asset and config counts, recent changes
- Export to CSV

### Audit & History
- Change log on every record (what changed and when)
- Config-to-asset assignment history

### Administration
- Bulk import assets and configs via CSV
- Django admin as fallback management interface

---

## Data Model Overview

```
Physical Asset (serial: ABC123)
    └── Config [type: physical] (hostname: hypervisor-01)
            └── Config [type: virtual] (hostname: vm-web-01)
                    └── VM Asset  →  effective serial = ABC123 (via host chain)
            └── Config [type: virtual] (hostname: vm-db-01)
                    └── VM Asset  →  effective serial = ABC123 (via host chain)

When physical asset is swapped to new hardware (serial: XYZ999):
    ConfigAssetHistory closes old record, opens new one pointing to XYZ999
    All VM effective serials now resolve to XYZ999 automatically
```

---

## Implementation Checklist

### Project Setup
- [ ] Initialize Django project
- [ ] Create `assets` app
- [ ] Configure SQLite in `settings.py`
- [ ] `requirements.txt`
- [ ] `.env` support for `SECRET_KEY` and `DEBUG`

### Models
- [ ] `Asset` — make, model, serial (nullable for VMs), type, status, location, notes
- [ ] `AssetType` — category lookup (desktop, laptop, server, virtual machine, etc.)
- [ ] `Location` — site, room
- [ ] `Vendor` — name, contact info, support URL
- [ ] `Purchase` — asset FK, vendor, cost, PO number, invoice, purchase date
- [ ] `Warranty` — asset FK, start date, end date
- [ ] `MaintenanceLog` — asset FK, date, description, performed by
- [ ] `Config` — hostname, OS, OS version, IP address, role, domain, config_type (physical/virtual), host_config FK (self, nullable — set for VM configs), notes
- [ ] `ConfigAssetHistory` — config FK, asset FK, assigned date, removed date
- [ ] `Config.effective_serial` — property that walks `host_config → ConfigAssetHistory → Asset.serial`; for physical configs resolves directly
- [ ] `Contact` — name, email, phone, department
- [ ] `Department` — name
- [ ] `ConfigAssignment` — config FK, contact FK, assigned date, returned date
- [ ] `AuditLog` — model, object id, field, old value, new value, timestamp

### Views & Templates
- [ ] Base template with nav sidebar
- [ ] Asset list view with search and filters (show effective serial for VM assets)
- [ ] Asset detail view
- [ ] Asset create/edit form (serial optional when type is virtual machine)
- [ ] Asset retire/dispose workflow
- [ ] Config list view with search and filters
- [ ] Config detail view (current asset, host config if VM, child VM configs if host, assignment history, contact)
- [ ] Config create/edit form (host config selector shown when type is virtual)
- [ ] Config swap — reassign config to a new physical asset
- [ ] Contact list and detail views
- [ ] Department list view
- [ ] Maintenance log entry form
- [ ] Dashboard (asset counts, config counts, recent activity)

### Auth
- [ ] Login / logout
- [ ] Protect all views behind login

### Import / Export
- [ ] CSV import for bulk asset creation
- [ ] CSV import for bulk config creation
- [ ] CSV export for filtered asset and config lists

### Testing
- [ ] Model unit tests
- [ ] `effective_serial` traversal tests (physical, VM, VM after host swap)
- [ ] Config swap logic tests
- [ ] View integration tests
- [ ] CSV import/export tests

### Deployment
- [ ] `Dockerfile` + `docker-compose.yml`
- [ ] Static file collection
- [ ] DB backup script for SQLite file
- [ ] README with setup instructions
