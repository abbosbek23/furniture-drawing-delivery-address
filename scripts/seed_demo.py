"""Run with `odoo shell -d furniture_demo` in the supplied Compose environment.

This opt-in script creates and confirms the sample order only in furniture_demo.
The module itself does not load demo records or change warehouse configuration.
"""

import base64
from pathlib import Path

from odoo import Command


def seed_demo(env):
    if env.cr.dbname != "furniture_demo":
        raise RuntimeError("This demo script only runs in the furniture_demo database.")

    def get_or_create(name, model, values):
        xmlid = f"furniture_attachment_demo.{name}"
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            return record
        record = env[model].with_context(no_reset_password=True).create(values)
        env["ir.model.data"].create(
            {"module": "furniture_attachment_demo", "name": name, "model": model, "res_id": record.id, "noupdate": True}
        )
        return record

    company = env.company
    warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
    if not warehouse:
        raise RuntimeError("Install the module and its Inventory dependencies first.")
    for number in (1, 2):
        get_or_create(
            f"store_{number}",
            "stock.location",
            {"name": f"Store {number}", "usage": "internal", "location_id": warehouse.lot_stock_id.id, "company_id": company.id},
        )
    get_or_create("workshop", "mrp.workcenter", {"name": "Furniture Workshop", "company_id": company.id})
    customer = get_or_create("customer", "res.partner", {"name": "Bahodir Furniture Client", "customer_rank": 1})
    mto = warehouse.mto_pull_id.route_id
    mto.active = True
    product = get_or_create(
        "kitchen",
        "product.product",
        {
            "name": "Custom Kitchen Furniture",
            "type": "consu",
            "is_storable": True,
            "list_price": 1000,
            "route_ids": [Command.set((mto | warehouse.manufacture_pull_id.route_id).ids)],
        },
    )
    component = get_or_create("panel", "product.product", {"name": "Furniture Panel", "type": "consu", "is_storable": True})
    get_or_create(
        "kitchen_bom",
        "mrp.bom",
        {
            "product_tmpl_id": product.product_tmpl_id.id,
            "company_id": company.id,
            "product_qty": 1,
            "type": "normal",
            "bom_line_ids": [Command.create({"product_id": component.id, "product_qty": 2})],
        },
    )
    order = get_or_create(
        "sale_order",
        "sale.order",
        {
            "partner_id": customer.id,
            "warehouse_id": warehouse.id,
            "client_order_ref": "FURNITURE-DEMO-001",
            "production_address": "Sho'rchi, Shaldiroq MFY",
            "order_attachment": base64.b64encode(Path("/mnt/demo-files/kitchen_measurement.pdf").read_bytes()),
            "attachment_name": "kitchen_measurement.pdf",
            "order_line": [Command.create({"product_id": product.id, "product_uom_qty": 1, "price_unit": 1000})],
        },
    )
    if order.state in ("draft", "sent"):
        order.action_confirm()
    production = env["mrp.production"].search([("sale_line_id", "in", order.order_line.ids)])
    if len(production) != 1:
        raise RuntimeError("Expected exactly one linked Manufacturing Order.")
    assert production.production_address == "Sho'rchi, Shaldiroq MFY"
    assert production.attachment_name == "kitchen_measurement.pdf"
    assert production.order_attachment == order.order_attachment

    # These credentials apply exclusively to the isolated, loopback-only demo.
    env.ref("base.user_admin").write({"login": "admin", "password": "furniture-demo"})
    get_or_create(
        "workshop_user",
        "res.users",
        {
            "name": "Workshop Demo User",
            "login": "workshop",
            "password": "workshop-demo",
            "company_id": company.id,
            "company_ids": [Command.set(company.ids)],
            "group_ids": [Command.set(env.ref("mrp.group_mrp_user").ids)],
        },
    )
    env.cr.commit()
    print(f"Demo ready: Sales Order {order.name} (id={order.id}), Manufacturing Order {production.name} (id={production.id}).")
    print("URL: http://localhost:8079 | admin / furniture-demo | workshop / workshop-demo")


seed_demo(env)
