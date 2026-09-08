# Furniture manufacturing demo for Odoo 19 Community

Complete custom addon: [sale_mrp_attachment_address](sale_mrp_attachment_address/README.md).
It shares a Sales Order's installation address and uploaded drawing with its
Manufacturing Order using Odoo's native `sale_mrp` relation.

- [Installation, demo steps, tests, Studio explanation, and GitHub upload instructions](sale_mrp_attachment_address/README.md)
- [Validation results](VALIDATION.md)
- [Sample measurement PDF](output/pdf/kitchen_measurement.pdf)
- [Docker Compose environment](compose.yaml)

## Run the demo

```bash
docker compose up -d db
docker compose run --rm odoo odoo -d furniture_demo \
  -i sale_mrp_attachment_address --without-demo --stop-after-init
docker compose run --rm -T odoo odoo shell \
  -d furniture_demo --no-http < scripts/seed_demo.py
docker compose up -d odoo
```

Open **http://localhost:8079** and pick a database at the login screen.

| Database | Purpose | Login | Password |
| --- | --- | --- | --- |
| `furniture_demo` | Seeded demo, addon already installed | `admin` | `furniture-demo` |
| `furniture_demo` | Manufacturing role, no sales access | `workshop` | `workshop-demo` |
| `furniture` | Clean database — install the app yourself from **Apps** | `admin` | `admin` |

These credentials, and the `furniture-master` database-manager password in
`config/odoo.conf`, are for the isolated local demo only.

## Install the app from the Apps screen

Create the clean database once, if it does not exist yet:

```bash
docker compose run --rm odoo odoo -d furniture -i base \
  --without-demo=all --stop-after-init
docker compose restart odoo
```

Then log in to `furniture`, open **Apps**, search for **Sales / Manufacturing
Address and Drawing**, and press **Activate**. The manifest sets
`application=True`, so the app is listed under the default Apps filter with its
own icon — no developer mode and no filter change required. Installing it pulls
in Sales and Manufacturing through the `sale_management` and `sale_mrp`
dependencies.

Odoo only re-reads the addons directory at startup, so run
`docker compose restart odoo` after adding or renaming a module.

The sample Sales Order is for **Bahodir Furniture Client**, product **Custom
Kitchen Furniture**, address **Sho'rchi, Shaldiroq MFY**, and attachment
**kitchen_measurement.pdf**. The seed confirms it and creates its MO.

## Run the checks

```bash
python3 scripts/check_syntax.py
docker compose run --rm odoo odoo -d furniture_test \
  -i sale_mrp_attachment_address --without-demo \
  --test-enable --test-tags=/sale_mrp_attachment_address \
  --stop-after-init --http-port=8070
```

Use `-u` instead of `-i` to rerun tests against an already installed database.
Use `docker compose down` to stop the demo and retain its data.
