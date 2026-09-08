import base64
from types import SimpleNamespace
from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestSaleMrpAttachmentAddress(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.address = "Sho'rchi, Shaldiroq MFY"
        cls.filename = "kitchen_measurement.pdf"
        cls.file_bytes = b"%PDF-1.4\nFurniture measurement test fixture\n%%EOF\n"
        cls.payload = base64.b64encode(cls.file_bytes)
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.mto = cls.warehouse.mto_pull_id.route_id
        cls.mto.active = True
        cls.manufacture = cls.warehouse.manufacture_pull_id.route_id
        cls.customer = cls.env["res.partner"].create(
            {"name": "Bahodir Furniture Client"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Custom Kitchen Furniture",
                "type": "consu",
                "is_storable": True,
                "list_price": 1000,
                "route_ids": [Command.set((cls.mto | cls.manufacture).ids)],
            }
        )
        cls.component = cls.env["product.product"].create(
            {"name": "Furniture Panel", "type": "consu", "is_storable": True}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product.product_tmpl_id.id,
                "product_qty": 1,
                "type": "normal",
                "bom_line_ids": [
                    Command.create({"product_id": cls.component.id, "product_qty": 2})
                ],
            }
        )
        cls.workshop_user = new_test_user(
            cls.env,
            login="furniture_test_workshop",
            groups="mrp.group_mrp_user",
            company_id=cls.env.company.id,
            company_ids=[Command.set(cls.env.company.ids)],
        )

    def _make_order(self, **values):
        return self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "warehouse_id": self.warehouse.id,
                "production_address": self.address,
                "order_attachment": self.payload,
                "attachment_name": self.filename,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 1000,
                        }
                    )
                ],
                **values,
            }
        )

    def _confirm_order(self, **values):
        order = self._make_order(**values)
        order.action_confirm()
        production = self.env["mrp.production"].search(
            [("sale_line_id", "in", order.order_line.ids)]
        )
        self.assertEqual(len(production), 1, "MTO + Manufacture must generate one MO")
        return order, production

    def _assert_information(self, production, address=None, payload=None, filename=None):
        self.assertEqual(production.production_address, address or self.address)
        self.assertEqual(
            production.with_context(bin_size=False).order_attachment,
            payload or self.payload,
        )
        self.assertEqual(production.attachment_name, filename or self.filename)

    def test_confirm_sale_creates_linked_manufacturing_order(self):
        order, production = self._confirm_order()
        self.assertEqual(order.state, "sale")
        self.assertEqual(production.state, "confirmed")
        self.assertEqual(production.sale_order_id, order)
        self._assert_information(production)
        self.assertEqual(
            self.env["ir.attachment"].search_count(
                [
                    ("res_model", "=", "sale.order"),
                    ("res_id", "=", order.id),
                    ("res_field", "=", "order_attachment"),
                ]
            ),
            1,
        )
        self.assertFalse(
            self.env["ir.attachment"].search_count(
                [
                    ("res_model", "=", "mrp.production"),
                    ("res_id", "=", production.id),
                    ("res_field", "=", "order_attachment"),
                ]
            )
        )

    def test_manual_manufacturing_form_can_select_sales_line(self):
        self.product.route_ids = [Command.clear()]
        order = self._make_order()
        order.action_confirm()
        with Form(self.env["mrp.production"]) as form:
            form.product_id = self.product
            form.bom_id = self.bom
            form.sale_line_id = order.order_line
        production = form.record
        self._assert_information(production)
        production.action_confirm()
        self._assert_information(production)

    def test_origin_text_does_not_guess_a_customer(self):
        order = self._make_order()
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product.id,
                "bom_id": self.bom.id,
                "origin": order.name,
            }
        )
        self.assertFalse(production.sale_order_id)
        self.assertFalse(production.production_address)
        self.assertFalse(production.order_attachment)
        self.assertFalse(production.attachment_name)

    def test_replacement_removal_and_address_changes_are_live(self):
        order, production = self._confirm_order()
        self._assert_information(production)  # Populate the related field cache first.
        revised = base64.b64encode(b"%PDF-1.4\nRevised measurements\n%%EOF\n")
        order.write(
            {
                "production_address": "Sho'rchi, revised installation address",
                "order_attachment": revised,
                "attachment_name": "kitchen_measurement_v2.pdf",
            }
        )
        self._assert_information(
            production,
            address=order.production_address,
            payload=revised,
            filename=order.attachment_name,
        )
        order.write(
            {"production_address": False, "order_attachment": False, "attachment_name": False}
        )
        self.assertFalse(production.production_address)
        self.assertFalse(production.order_attachment)
        self.assertFalse(production.attachment_name)

    def test_manufacturing_user_can_read_and_download_without_sales_role(self):
        _order, production = self._confirm_order()
        self.assertFalse(self.workshop_user.has_group("sales_team.group_sale_salesman"))
        self.env.invalidate_all()
        production = production.with_user(self.workshop_user)
        self._assert_information(production)
        # Exercise the same record/field checks and streaming used by /web/content.
        binary = self.env["ir.binary"].with_user(self.workshop_user)
        record = binary._find_record(
            res_model="mrp.production", res_id=production.id, field="order_attachment"
        )
        with patch("odoo.http.request", new=SimpleNamespace(env=production.env)):
            stream = binary._get_stream_from(
                record, "order_attachment", filename_field="attachment_name"
            )
        self.assertEqual(stream.download_name, self.filename)
        self.assertEqual(stream.data, self.file_bytes)
        self.assertEqual(stream.mimetype, "application/pdf")

    def test_other_company_link_is_rejected(self):
        order = self._make_order()
        other_company = self.env["res.company"].create({"name": "Other Furniture Company"})
        other_warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", other_company.id)], limit=1
        )
        with self.assertRaises(UserError), self.cr.savepoint():
            self.env["mrp.production"].with_company(other_company).create(
                {
                    "company_id": other_company.id,
                    "picking_type_id": other_warehouse.manu_type_id.id,
                    "product_id": self.product.id,
                    "bom_id": self.bom.id,
                    "sale_line_id": order.order_line.id,
                }
            )

    def test_unlinking_and_relinking_refreshes_information(self):
        order = self._make_order()
        other_order = self._make_order(production_address="Second customer address")
        production = self.env["mrp.production"].create(
            {"product_id": self.product.id, "bom_id": self.bom.id, "sale_line_id": order.order_line.id}
        )
        self._assert_information(production)
        production.sale_line_id = other_order.order_line
        self.assertEqual(production.production_address, "Second customer address")
        production.sale_line_id = False
        self.assertFalse(production.production_address)
        self.assertFalse(production.order_attachment)
        self.assertFalse(production.attachment_name)

    def test_duplication_does_not_reuse_customer_file(self):
        order, production = self._confirm_order()
        duplicate_order = order.copy()
        self.assertFalse(duplicate_order.production_address)
        self.assertFalse(duplicate_order.order_attachment)
        self.assertFalse(duplicate_order.attachment_name)
        duplicate_mo = production.copy()
        self.assertFalse(duplicate_mo.sale_line_id)
        self.assertFalse(duplicate_mo.production_address)
        self.assertFalse(duplicate_mo.order_attachment)

    def test_backorder_keeps_native_sales_link(self):
        order, production = self._confirm_order()
        backorder = production.copy(default=production._get_backorder_mo_vals())
        self.assertEqual(backorder.sale_order_id, order)
        self._assert_information(backorder)

    def test_combined_views_expose_groups_and_filename_widgets(self):
        cases = (
            ("sale.order", "sale.view_order_form", "production_information", self.env.user),
            (
                "mrp.production",
                "mrp.mrp_production_form_view",
                "sales_information",
                self.workshop_user,
            ),
        )
        for model, xmlid, group, user in cases:
            with self.subTest(model=model):
                view = self.env[model].with_user(user).get_view(
                    view_id=self.env.ref(xmlid).id, view_type="form"
                )
                arch = etree.fromstring(view["arch"])
                self.assertEqual(len(arch.xpath(f"//group[@name='{group}']")), 1)
                for field in ("production_address", "order_attachment", "attachment_name"):
                    self.assertTrue(arch.xpath(f"//group[@name='{group}']/field[@name='{field}']"))
                self.assertTrue(
                    arch.xpath(
                        f"//group[@name='{group}']/field[@name='order_attachment']"
                        "[@widget='binary'][@filename='attachment_name']"
                    )
                )
