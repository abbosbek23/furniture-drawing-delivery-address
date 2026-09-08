# Sales / Manufacturing Address and Drawing

An Odoo 19 Community module for furniture manufacturers. It carries the customer's
installation address and the uploaded drawing from the Sales Order through to the
Manufacturing Order, so the workshop reads them on the order it is actually building.

**Technical name:** `sale_mrp_attachment_address` · **Odoo:** 19.0 Community · **License:** LGPL-3

<p align="center">
  <img src="sale_mrp_attachment_address/static/description/icon.png" width="120" alt="Module icon">
</p>

## The problem it solves

The address where a kitchen or wardrobe gets installed, and the measurement drawing
it is built from, live on the Sales Order. The workshop works from the Manufacturing
Order, which shows neither. Most companies bridge that gap by hand — a separate Excel
sheet, a chat message, a printed drawing — and the workshop ends up building from a
stale copy.

This module removes the bridge. The address and the file are entered once by the
salesperson and read directly on the linked Manufacturing Order.

## Features

- **Production Information** group on the Sales Order — installation address plus one
  uploaded drawing, measurement PDF, image, or technical file.
- **Sales Information** group on the Manufacturing Order — originating order, its
  address, and the same file, ready to download.
- Values are read live through Odoo's native `sale_mrp` sales-line link, so correcting
  an address on the order immediately corrects what the workshop sees.
- Manufacturing users can open and download the drawing **without** being given a
  Sales role.
- A Sales Order Line selector for manually created draft Manufacturing Orders.
- The file is stored once, on the Sales Order — never duplicated onto the MO.
- No new models and no new access rules; existing Sales and Manufacturing permissions
  stay in force.

## Requirements

Odoo **19.0**. Developed and verified on Community; its dependencies
`sale_management` and `sale_mrp` are standard Community modules present in Enterprise
too, and are installed automatically.

Earlier Odoo versions are not supported: the module uses 19.0 view identifiers and
the current `readonly="..."` attribute syntax.

## Installation

1. Copy the whole `sale_mrp_attachment_address` directory into a directory listed in
   your `addons_path`, for example `/opt/odoo/custom-addons/`. Make sure the Odoo
   service user can read the files.
2. Restart Odoo. It reads the addons directory only at startup.
3. Open **Apps**, search for **Sales / Manufacturing Address and Drawing**, and press
   **Activate**.

The module is declared as an application, so it appears under the default **Apps**
filter with its own icon — no developer mode and no filter change needed. If it is
not listed, Odoo has not re-read the directory: restart the service, or enable
developer mode once and use **Apps → Update Apps List**.

Command-line install, if you prefer it:

```bash
odoo -c /etc/odoo/odoo.conf -d YOUR_DATABASE \
  -i sale_mrp_attachment_address --stop-after-init
```

Use `-u` in place of `-i` to upgrade an already installed database.

## How to use it

1. On a quotation, fill in **Production Address** and upload the drawing under
   **Production Information**.
2. Confirm the order. With a Manufacture route and a Bill of Materials, Odoo's
   standard procurement creates the Manufacturing Order and records the sales line
   on it.
3. Open the Manufacturing Order. **Sales Information** shows the originating order,
   the address, and the file — download it from there.

For a Manufacturing Order created by hand, select the confirmed order's **Sales Order
Line** on the draft MO and save; the address and file follow from it.

The MO shows **live values, not a snapshot**. Editing the Sales Order also changes
what an already completed MO displays. Drawing revisions and immutable production
approvals would be a separate feature.

## Documentation

- [Full module documentation](sale_mrp_attachment_address/README.md) — fields, security
  model, supported links and their limits, manual test scenarios, and an honest
  comparison with doing this in Odoo Studio
- [Verification results](VALIDATION.md) — what was tested and what the runs produced
- [Sample measurement PDF](output/pdf/kitchen_measurement.pdf)

## Tests

Ten integration tests cover automatic procurement, a manually saved MO form, unlinked
records, live replacement and removal, workshop file streaming, company mismatch
rejection, relinking, duplication, backorders, and both form views.

```bash
odoo -c /etc/odoo/odoo.conf -d YOUR_TEST_DATABASE \
  -i sale_mrp_attachment_address \
  --test-enable --test-tags=/sale_mrp_attachment_address --stop-after-init
```

A successful run reports **0 failed, 0 error(s)**. A dependency-free syntax and
manifest check is also available:

```bash
python3 scripts/check_syntax.py
```

## Local sandbox

This repository also carries a self-contained Docker environment for evaluating the
module without touching an existing Odoo installation — Odoo 19 plus PostgreSQL 16,
a script that seeds one sample order, and a sample measurement PDF.

```bash
docker compose up -d db

# clean database: install the module yourself from the Apps screen
docker compose run --rm odoo odoo -d furniture -i base \
  --without-demo=all --stop-after-init

# pre-loaded database: module installed and one sample order seeded
docker compose run --rm odoo odoo -d furniture_demo \
  -i sale_mrp_attachment_address --without-demo --stop-after-init
docker compose run --rm -T odoo odoo shell \
  -d furniture_demo --no-http < scripts/seed_demo.py

docker compose up -d odoo
```

Open **http://localhost:8079** and pick a database at the login screen.

| Database | Contents | Login | Password |
| --- | --- | --- | --- |
| `furniture` | Empty — install the module from **Apps** | `admin` | `admin` |
| `furniture_demo` | Module installed, one sample order | `admin` | `furniture-demo` |
| `furniture_demo` | Manufacturing role, no sales access | `workshop` | `workshop-demo` |

The seeded order is for **Bahodir Furniture Client**, product **Custom Kitchen
Furniture**, address **Sho'rchi, Shaldiroq MFY**, with **kitchen_measurement.pdf**
attached; the script confirms it and lets Odoo create the Manufacturing Order.

These logins, and the `furniture-master` database-manager password in
`config/odoo.conf`, belong to this throwaway local environment only. The web port is
bound to loopback and PostgreSQL publishes no host port. Use your own configuration
and credentials for a real installation.

`docker compose stop` shuts the sandbox down and keeps its data; `docker compose down -v`
removes it entirely.

## License

LGPL-3, matching the `license` declared in the module manifest.
