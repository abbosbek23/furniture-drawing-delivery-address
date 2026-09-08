# Validation results

Environment: Odoo 19.0-20260817 Community + PostgreSQL 16, `compose.yaml`,
Apple Silicon (linux/arm64). Raw logs live in `.validation/`.

## Automated tests — 10 passed, 0 failed, 0 errors

```bash
docker compose run --rm odoo odoo -d furniture_test \
  -u sale_mrp_attachment_address --without-demo \
  --test-enable --test-tags=/sale_mrp_attachment_address \
  --stop-after-init --http-port=8070
```

| Test | Covers |
| --- | --- |
| `test_confirm_sale_creates_linked_manufacturing_order` | `sale_mrp` link carries address + drawing to the MO |
| `test_manual_manufacturing_form_can_select_sales_line` | Manually created MO can pick a sales line |
| `test_origin_text_does_not_guess_a_customer` | A free-text `origin` never fabricates a customer link |
| `test_replacement_removal_and_address_changes_are_live` | Related fields follow SO edits with no re-confirm |
| `test_manufacturing_user_can_read_and_download_without_sales_role` | Workshop role reads and downloads without sales access |
| `test_other_company_link_is_rejected` | `_check_company` blocks cross-company links in draft |
| `test_unlinking_and_relinking_refreshes_information` | Unlink clears, relink restores |
| `test_duplication_does_not_reuse_customer_file` | `copy=False` keeps a duplicated SO clean |
| `test_backorder_keeps_native_sales_link` | Backorders retain the sales line |
| `test_combined_views_expose_groups_and_filename_widgets` | View arch exposes groups and filename widgets |

Log history: `.validation/install-tests.log` (2 failures, first pass),
`.validation/update-tests.log` and `.validation/final-install-tests.log` (green
after fixes), `.validation/rerun-tests.log` (green re-run on the current tree).

## Manual verification

- Fresh install into `furniture_demo` — `.validation/demo-install.log`
- Seed script created SO `S00001` and MO `WH/MO/00001` — `.validation/demo-seed.log`
- Runtime read-back through `odoo shell` on the running demo database:
  `MO WH/MO/00001 → SO S00001`, address `Sho'rchi, Shaldiroq MFY`,
  file `kitchen_measurement.pdf` (3164 bytes)
- Attachment download over HTTP as the workshop user — `scripts/test_http_download.py`
- Sample PDF rendered — `.validation/pdf-render.log`, `output/pdf/kitchen_measurement.pdf`
- Web UI reachable at http://localhost:8079 (HTTP 200 on `/web/login`)

## Apps-screen installation

Verified against the clean `furniture` database over authenticated JSON-RPC,
exercising the same `ir.module.module.button_immediate_install` the **Activate**
button calls:

- The app is listed with `application=True`, so it appears under the default
  **Apps** filter without developer mode
- `/sale_mrp_attachment_address/static/description/icon.png` is served — HTTP
  200, 9296 bytes, `image/png`
- Install completed in 17s and pulled in `sale_management`, `sale_mrp`, and
  `mrp`; `production_address`, `order_attachment`, and `attachment_name` were
  present on `sale.order` afterwards
- The `furniture` database was then dropped and re-created from `base` only, so
  it ships uninstalled and ready for a hands-on install

## Known local-environment note

Odoo runs threaded (`workers = 0`), where the watchdog counts the long-lived
`/websocket` request against `limit_time_real` and reloads the server roughly
every two minutes, dropping the open session. `config/odoo.conf` therefore sets
`limit_time_real = 0`. Keep the default limit in any production deployment,
which should run `workers > 0` with the websocket served on 8072 instead.
