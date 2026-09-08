# Sales / Manufacturing Address and Drawing

**Technical name:** `sale_mrp_attachment_address`  
**Version:** `19.0.1.0.0`  
**Target:** Odoo 19 Community  
**License:** LGPL-3

## Description

Replace the separate Excel handoff between sales and the furniture workshop.
Salespeople enter a customer installation address and upload a drawing on the
Sales Order. The linked Manufacturing Order displays the current address and
offers the same file for download.

The company can operate one warehouse, two stores, and one workshop. These are
normal Inventory locations and Manufacturing work centers; the addon does not
create or modify the company's logistics configuration during installation.

## Features

- A **Production Information** group on the Sales Order form.
- A **Sales Information** group on the Manufacturing Order form.
- One uploaded PDF, image, drawing, or other technical file per Sales Order.
- A filename-aware upload/download widget on both forms.
- Automatic links for Odoo's standard MTO manufacturing flow.
- A Sales Order Line selector for manually created draft Manufacturing Orders.
- Read-only, live related values on Manufacturing Orders, including the filename.
- An immediate company consistency check for the sales line, including draft MOs.
- No duplicated binary files on Manufacturing Orders.
- Integration tests for the business workflow, views, streaming, and updates.

## Models and fields

| Model | Field | Type | Source / behavior |
| --- | --- | --- | --- |
| `sale.order` | `production_address` | Char | Entered by the salesperson |
| `sale.order` | `order_attachment` | Binary | Stored as an Odoo attachment |
| `sale.order` | `attachment_name` | Char | Set by the file widget |
| `mrp.production` | `sale_line_id` | Many2one | Existing `sale_mrp` link; company validation added |
| `mrp.production` | `sale_order_id` | Many2one | Related to `sale_line_id.order_id` |
| `mrp.production` | `production_address` | Char | Related to `sale_line_id.order_id.production_address` |
| `mrp.production` | `order_attachment` | Binary | Related to `sale_line_id.order_id.order_attachment` |
| `mrp.production` | `attachment_name` | Char | Related to `sale_line_id.order_id.attachment_name` |

### Why `origin.production_address` cannot be used

In Odoo 19, `mrp.production.origin` is a **Char** containing a source document
label, not a relational field. Odoo cannot traverse it in a `related` path.
Declaring `related="origin.production_address"` would prevent module loading.

This addon depends on `sale_management` to activate the Sales application menu,
and the official Community `sale_mrp` module, which propagates
the Sales Order Line into Manufacturing Orders during procurement. The working
relation is:

```text
mrp.production.sale_line_id -> sale.order.line.order_id -> sale.order
```

This uses record IDs and avoids guessing a customer from free-text document
names. See the official Odoo 19 [MRP sales link](https://github.com/odoo/odoo/blob/19.0/addons/sale_mrp/models/mrp_production.py)
and [procurement propagation](https://github.com/odoo/odoo/blob/19.0/addons/sale_mrp/models/stock_rule.py).

### View compatibility

The addon inherits the following Odoo 19 external IDs:

| Form | External ID | Official source |
| --- | --- | --- |
| Sales Order | `sale.view_order_form` | [sale_order_views.xml](https://github.com/odoo/odoo/blob/19.0/addons/sale/views/sale_order_views.xml) |
| Manufacturing Order | `mrp.mrp_production_form_view` | [mrp_production_views.xml](https://github.com/odoo/odoo/blob/19.0/addons/mrp/views/mrp_production_views.xml) |

Both groups are inserted immediately before the form's main notebook, using
`//form/sheet/notebook`. The views use current `readonly` expressions, with no
legacy `attrs` or `states` syntax.

## Installation on Odoo 19

### Existing Odoo 19 Community server

1. Copy the **whole** `sale_mrp_attachment_address` directory into a custom
   addons directory, for example `/opt/odoo/custom-addons/`.
2. Add that parent directory to `addons_path` in your Odoo configuration,
   preserving the existing core addons paths. Ensure the Odoo service user can
   read the module files.
3. Stop the Odoo application workers, then install from the configured Odoo
   environment. Adjust the executable, configuration, and database paths:

   ```bash
   /opt/odoo/odoo-bin -c /etc/odoo/odoo.conf \
     -d furniture \
     -i sale_mrp_attachment_address \
     --stop-after-init
   ```

4. Start Odoo again and sign in. Sales, Inventory, Manufacturing, and their
   integration dependencies are installed through `sale_management` and
   `sale_mrp` automatically.
5. Alternatively, install it from the web interface. Restart Odoo after copying
   the addon, open **Apps**, search for **Sales / Manufacturing Address and
   Drawing**, and press **Activate**. The manifest sets `application=True`, so
   the app appears under the default **Apps** filter with its own icon; no
   developer mode and no filter change are needed. If it is not listed yet,
   Odoo has not re-read the addons directory: restart the service, or enable
   developer mode once and use **Apps -> Update Apps List**.

   Installing it pulls in Sales and Manufacturing automatically through the
   `sale_management` and `sale_mrp` dependencies.

For subsequent updates, stop application workers, run the same command with
`-u sale_mrp_attachment_address` in place of `-i`, and restart them.

This is a Python server addon. Install it on a server or container where custom
addons can be loaded; uploading the ZIP as an attachment does not install it.

### Local demo with Docker Compose

The repository includes `compose.yaml`, a sample PDF, and an optional seed
script. Run the following from the repository root:

```bash
docker compose up -d db
docker compose run --rm odoo odoo \
  --database=furniture_demo \
  --init=sale_mrp_attachment_address \
  --without-demo \
  --stop-after-init
docker compose run --rm -T odoo odoo shell \
  --database=furniture_demo --no-http < scripts/seed_demo.py
docker compose up -d odoo
```

Open **http://localhost:8079**.

| Demo account | Login | Password |
| --- | --- | --- |
| Administrator / sales and manufacturing | `admin` | `furniture-demo` |
| Workshop user / Manufacturing role | `workshop` | `workshop-demo` |

These are disposable local demo credentials. The web port is bound to loopback
and PostgreSQL has no published host port. Use your normal private configuration
and credentials for a production installation.

The seed script only accepts the database name `furniture_demo`. It creates the
specified customer, a manufactured kitchen product, a simple BoM, two store
stock locations, and one workshop work center. It uses the company's existing
warehouse and confirms one sample order. Re-running it reuses its demo records;
it also resets the demo admin password to the value above. No emails are sent by
the script. It does not install Point of Sale or configure store replenishment.

Stop the local services while retaining their database and uploaded files:

```bash
docker compose down
```

## How it works

1. Sales saves the address and one attachment on a quotation or an unlocked
   confirmed Sales Order. The file widget maintains `attachment_name`.
2. With a suitable BoM and the MTO manufacturing flow, confirming the Sales
   Order creates an MO through Odoo procurement. `sale_mrp` sets `sale_line_id`.
3. The MO reads all three values through that line's Sales Order. Editing,
   replacing, or removing the source data is reflected when the MO is reloaded.
4. The file is stored once against the Sales Order (`attachment=True`). The
   MO's non-stored related Binary uses `attachment=False` so Odoo streams the
   related bytes instead of looking for a nonexistent attachment on the MO.

The MO values are live references, **not historical snapshots**. Updating a
Sales Order also changes the information displayed on an already completed MO.
Drawing revisions or immutable production approvals would be a separate feature.

### Access rights

No new models are created. The header-only `security/ir.model.access.csv` is
included for the requested structure and intentionally omitted from manifest
data: it grants no additional permissions. Existing Sales, Manufacturing, and
company record rules remain in force.

The SO fields are limited to internal users; the MO information is limited to
Manufacturing users. Related fields explicitly compute with elevated read
access to supply those workshop details. The Sales Order/Line widgets are shown
to users who also have a Sales role. Manufacturing users can download the file
from the MO without being assigned a Sales role.

The underlying `sale_mrp` dependency already grants Manufacturing users some
Sales Order and Sales Order Line access. This addon does not claim to isolate all
commercial sales data or add a new security boundary around it. Its related
fields are read-only in the MO form; normal model/API permissions still apply.

### Supported links and limits

- **Automatic:** Standard MTO procurement carries the sales line into the MO.
- **Manual:** A planner with both Sales and Manufacturing access selects the
  confirmed order's matching **Sales Order Line** on a draft MO and saves it.
- Entering a Sales Order number only in **Source** (`origin`) does not link it.
- A stock replenishment MO without `sale_line_id` shows empty sales information.
- One MO displays one originating sales line's order information. Merged demand
  from several customers and multi-level component order attribution need a
  separate business rule; this addon does not arbitrarily select an order.
- Standard backorders retain the native sales link. Normal duplication clears
  it. Duplicating a Sales Order clears its custom address and file.
- One file is supported; replacing it replaces the current drawing. Chatter
  attachments and multiple-file document management are separate features.

## Demo scenario and manual testing

### Configure manufacturing

1. Enable **Replenish on Order (MTO)** in Inventory settings.
2. Create **Custom Kitchen Furniture** as a Goods product with inventory
   tracking enabled, then create a **Manufacture this Product** BoM with at
   least one component (for example, two Furniture Panels).
3. Enable **Replenish on Order (MTO)** for the product and make sure the
   warehouse can manufacture it. Odoo 19 may hide the Manufacture route in the
   product form and infer manufacturing from the BoM. To select routes explicitly,
   enable Multi-Step Routes and make Manufacture applicable to Products.

These are Odoo 19's standard [MTO setup and manufacturing steps](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/mto.html).
The optional seed script performs this configuration for its demo product.

### Verify the requested workflow

1. Create customer **Bahodir Furniture Client**.
2. Create a Sales Order with one **Custom Kitchen Furniture**.
3. In **Production Information**, enter:

   | Field | Value |
   | --- | --- |
   | Production Address | `Sho'rchi, Shaldiroq MFY` |
   | Drawing / File Attachment | `kitchen_measurement.pdf` |

   Use the supplied `output/pdf/kitchen_measurement.pdf` or your own sample file.
4. Save and confirm the order.
5. Open the resulting MO using the **Manufacturing** smart button on the order,
   or go to **Manufacturing -> Operations -> Manufacturing Orders**.
6. In **Sales Information**, verify the exact address and filename above.
7. Download the file from the MO and confirm it opens and matches the SO file.
8. Change the address and replace the attachment on the unlocked SO. Reload the
   MO and verify the updated address, filename, and downloaded contents.
9. Remove the uploaded file on the SO, save, and reload the MO: there should be
   no file to download. Restore it if continuing the demo.
10. Repeat the MO view and download check as the **Workshop Demo User**.

### Manually created Manufacturing Order

Use a **separate** confirmed Sales Order that has not already generated an MO
(for example, without MTO). Go to Manufacturing, create a draft MO, select the
same product and BoM, and select its **Sales Order Line** under **Sales
Information**. Save and confirm the MO. The address and file must match that
Sales Order. The selector requires both Sales and Manufacturing roles and is
editable only while the MO is in draft.

Creating another MO after MTO has already generated one would duplicate demand.

## Automated tests

### Syntax checks (no Odoo installation required)

From the repository root:

```bash
python3 scripts/check_syntax.py
```

This compiles Python source and parses XML, and checks manifest paths and the
ACL header. It does not replace installation or ORM integration tests.

### Odoo integration tests

Run against a dedicated test database. With the included Compose setup:

```bash
docker compose up -d db
docker compose run --rm odoo odoo \
  --database=furniture_test \
  --init=sale_mrp_attachment_address \
  --without-demo \
  --test-enable \
  --test-tags=/sale_mrp_attachment_address \
  --stop-after-init --http-port=8070
```

For repeat runs on an installed test database, replace
`--init=sale_mrp_attachment_address` with `--update=sale_mrp_attachment_address`.
For a source installation, use the same Odoo arguments with your `odoo-bin` and
configuration file. Successful output includes **0 failed, 0 error(s)**.

The ten integration tests cover automatic procurement, a manually saved MO
form, empty/unlinked records, live replacement/removal, workshop file streaming,
company mismatch rejection, relinking, duplication, backorders, and both combined
form views. The file streaming test supplies an HTTP request context while
exercising Odoo's actual record access checks and binary stream implementation.

See the repository's `VALIDATION.md` for the actual verified runtime and results.

### Real HTTP download checks

With the seeded demo running at `localhost:8079`:

```bash
python3 scripts/test_http_download.py
```

This logs in independently as both demo users, reads the linked MO, verifies
the downloaded PDF byte-for-byte and its download filename, and checks that an
anonymous request cannot obtain the drawing. It uses only Python's standard
library and does not change the demo order.

## Can this be done with Odoo Studio?

**Yes, in an edition that includes Studio:** it can add custom fields and make
simple form changes. Studio also supports related fields when a usable relation
already exists; it would be inaccurate to say that Studio cannot create related
fields at all. See Odoo's [Studio field documentation](https://www.odoo.com/documentation/19.0/applications/studio/fields.html).

There are three practical limits here:

1. **Automatic relations:** Drawing a field on a form does not implement
   procurement linkage. Studio needs an existing relation, such as the standard
   `sale_mrp` sales line, or an automation that reliably sets a new relation.
2. **Related fields:** Studio follows existing relational paths. It cannot turn
   the text `origin` field into a relationship merely by adding a related field.
   File storage and download behavior also need validation.
3. **Custom business logic:** Company validation, alternative procurement flows,
   lifecycle rules, and regression tests are easier to control and review in a
   versioned Python addon than in database-specific manual configuration.

Official Odoo Studio is an Enterprise feature, not part of the requested
Community installation; see the [edition comparison](https://www.odoo.com/page/editions).
Custom development fits this project because it runs on Community, preserves
the exact requested technical field names, makes installation repeatable, and
includes explicit binary behavior and automated tests. In Enterprise, a basic
equivalent may be possible in Studio using the existing `sale_mrp` relation.

## Upload to GitHub

Run these commands from the repository root after creating an **empty** GitHub
repository. Replace `YOUR_ACCOUNT` with your account or organization:

```bash
git init -b main
git add .gitignore compose.yaml README.md VALIDATION.md \
  sale_mrp_attachment_address scripts output/pdf/kitchen_measurement.pdf
git commit -m "Add Odoo 19 furniture sales and manufacturing addon"
git remote add origin https://github.com/YOUR_ACCOUNT/mebel-furniture.git
git push -u origin main
```

If the directory is already a repository, skip `git init`; if `origin` already
exists, inspect it with `git remote -v` and use the intended repository. Log in
using your usual GitHub credential manager or SSH setup. The provided
`.gitignore` excludes local test logs, caches, environment secrets, and archives.
This delivery supplies instructions; it does not publish a repository.

## Module layout

```text
sale_mrp_attachment_address/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── sale_order.py
│   └── mrp_production.py
├── views/
│   ├── sale_order_views.xml
│   └── mrp_production_views.xml
├── security/
│   └── ir.model.access.csv
├── static/
│   └── description/
│       ├── icon.png
│       └── index.html
├── tests/
│   ├── __init__.py
│   └── test_sale_mrp_attachment_address.py
└── README.md
```
