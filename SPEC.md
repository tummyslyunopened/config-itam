# config-itam

IT Asset Management system — SQLite DB with Django WebUI for tracking hardware assets across an organization.

Single application user (Django's built-in auth). Each asset has a contact person who does not need to be an app user.

Configuration is decoupled from physical hardware — a `Config` record is automatically created whenever a new `Asset` is created, and can be reassigned to a different physical `Asset` when hardware is replaced.

Virtual machines are tracked as assets whose serial number is derived through their config relationship to a host, not stored directly.

---

## Features

### Asset Inventory
- Register physical machines (desktops, laptops, servers, peripherals)
- Register virtual machine assets (no physical serial of their own)
- Track make, model, serial number, and purchase date for physical assets
- Track physical location (site, room)
- Asset status: active, spare, in-repair, retired, disposed
- Creating a new asset automatically creates a linked empty `Config`

### Configuration Management
- `Config` represents the logical identity of a machine, independent of hardware
- Each config carries a single `data` JSONField of arbitrary shape — the exact schema is not enforced by the application, as deployment strategy is not yet decided
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
- Search and filter configs by name, type, host
- Dashboard with asset and config counts, recent changes
- Export to CSV

### Audit & History
- Change log on every record (what changed and when)
- Config-to-asset assignment history

### Reference Data Management
- Full CRUD for **Locations** (site, room) via the UI
- Full CRUD for **Asset Types** (name, is_virtual flag) via the UI
- These are managed in a dedicated Settings section in the sidebar

### Administration
- Bulk import assets via CSV
- Django admin as fallback management interface

---

## Data Model Overview

```
Physical Asset (serial: ABC123)
    └── Config [type: physical] (data: {...})
            └── Config [type: virtual] (data: {...})
                    └── VM Asset  →  effective serial = ABC123 (via host chain)
            └── Config [type: virtual] (data: {...})
                    └── VM Asset  →  effective serial = ABC123 (via host chain)

When physical asset is swapped to new hardware (serial: XYZ999):
    ConfigAssetHistory closes old record, opens new one pointing to XYZ999
    All VM effective serials now resolve to XYZ999 automatically

When a new Asset is created:
    A new empty Config (data: {}) is automatically created and linked to it
```

---

## Implementation Checklist

### Project Setup
- [x] Initialize Django project
- [x] Create `assets` app
- [x] Configure SQLite in `settings.py`
- [x] `requirements.txt`
- [x] `.env` support for `SECRET_KEY` and `DEBUG`

### Models
- [x] `Asset` — make, model, serial (nullable for VMs), type, status, location, notes
- [x] `AssetType` — category lookup (desktop, laptop, server, virtual machine, etc.)
- [x] `Location` — site, room
- [x] `Vendor` — name, contact info, support URL
- [x] `Purchase` — asset FK, vendor, cost, PO number, invoice, purchase date
- [x] `Warranty` — asset FK, start date, end date
- [x] `MaintenanceLog` — asset FK, date, description, performed by
- [x] `Config` — name (optional label), config_type (physical/virtual), host_config FK (self, nullable), data (JSONField, arbitrary shape), notes
- [x] `ConfigAssetHistory` — config FK, asset FK, assigned date, removed date
- [x] `Config.effective_serial` — property that walks `host_config → ConfigAssetHistory → Asset.serial`; for physical configs resolves directly
- [x] `Contact` — name, email, phone, department
- [x] `Department` — name
- [x] `ConfigAssignment` — config FK, contact FK, assigned date, returned date
- [x] `AuditLog` — model, object id, field, old value, new value, timestamp

### Views & Templates
- [x] Base template with nav sidebar
- [x] Asset list view with search and filters (show effective serial for VM assets)
- [x] Asset detail view
- [x] Asset create/edit form — auto-creates linked Config on new asset creation
- [x] Asset retire/dispose workflow
- [x] Config list view with search and filters
- [x] Config detail view (current asset, host config if VM, child VM configs if host, assignment history, contact)
- [x] Config create/edit form (host config selector shown when type is virtual; data edited as raw JSON textarea)
- [x] Config swap — reassign config to a new physical asset
- [x] Contact list and detail views
- [x] Department list view
- [x] Maintenance log entry form
- [x] Location list, create, edit views
- [x] AssetType list, create, edit views
- [x] Dashboard (asset counts, config counts, recent activity)

### Auth
- [x] Login / logout
- [x] Protect all views behind login

### Import / Export
- [x] CSV import for bulk asset creation
- [x] CSV export for asset and config lists

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
