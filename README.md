# config-itam

A personal IT Asset Management app — Django + SQLite — for tracking hardware
and the logical configs that ride on top of it.

The defining idea: **`Config` is decoupled from `Asset`.** A `Config` is the
logical identity of a machine; an `Asset` is the physical (or virtual) box. A
new Asset auto-creates an empty linked Config; when hardware is replaced, you
reassign the Config to the new Asset and history is preserved.

## Setup

**Requirements:** Python 3.11+

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and sign in.

## Highlights

- **Asset inventory** — make, model, serial, location, status (active / spare
  / in-repair / retired / disposed); creating an asset auto-creates a linked
  empty `Config`.
- **Configs decoupled from hardware** — reassign a `Config` to a new `Asset`
  when hardware is replaced; full assignment history retained.
- **Virtual machine tracking** — a VM `Asset` has no serial of its own; its
  effective serial is derived through `VM Asset → VM Config → host Config →
  current physical Asset → serial`. Swap the host's hardware and every VM's
  effective serial updates automatically.
- **Lifecycle** — purchase info, warranty dates, maintenance log,
  retirement / disposal workflow with audit trail.
- **Contacts & departments** — a contact directory grouped by department;
  configs are assigned to contacts (not to physical assets).
- **Reference data** — full CRUD for Locations and Asset Types in the UI;
  Django admin available as fallback.
- **Search, CSV export, bulk CSV import**, plus an audit log on every record.

## Data model in one picture

```
Physical Asset (serial: ABC123)
    └── Config [physical]
            ├── Config [virtual]  →  VM Asset  (effective serial: ABC123)
            └── Config [virtual]  →  VM Asset  (effective serial: ABC123)

Swap host to new hardware (serial: XYZ999):
    ConfigAssetHistory closes old record, opens new one pointing to XYZ999.
    All VM effective serials now resolve to XYZ999 automatically.
```

See `SPEC.md` for the full feature spec and implementation checklist.

## Where it lives

Vendored as a submodule of
[`tummyslyunopened/config`](https://github.com/tummyslyunopened/config).
