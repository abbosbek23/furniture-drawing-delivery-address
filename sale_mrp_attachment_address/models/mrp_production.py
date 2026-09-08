from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # Extend sale_mrp's native procurement link, retaining its other attributes.
    sale_line_id = fields.Many2one(check_company=True)
    sale_order_id = fields.Many2one(
        string="Sales Order",
        related="sale_line_id.order_id",
        readonly=True,
        groups="sales_team.group_sale_salesman",
    )
    production_address = fields.Char(
        string="Production Address",
        related="sale_line_id.order_id.production_address",
        readonly=True,
        store=False,
        compute_sudo=True,
        groups="mrp.group_mrp_user",
    )
    order_attachment = fields.Binary(
        string="Drawing / File Attachment",
        related="sale_line_id.order_id.order_attachment",
        readonly=True,
        store=False,
        # The file belongs to the SO. An MO-local attachment lookup would fail
        # when /web/content streams this non-stored related field.
        attachment=False,
        compute_sudo=True,
        groups="mrp.group_mrp_user",
    )
    attachment_name = fields.Char(
        string="File Name",
        related="sale_line_id.order_id.attachment_name",
        readonly=True,
        store=False,
        compute_sudo=True,
        groups="mrp.group_mrp_user",
    )

    @api.constrains("sale_line_id", "company_id")
    def _check_sales_line_company(self):
        # Core MRP checks companies at confirmation; protect draft links too.
        self._check_company(fnames=["sale_line_id"])
