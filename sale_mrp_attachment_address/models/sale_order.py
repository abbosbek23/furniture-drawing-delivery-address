from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    production_address = fields.Char(
        string="Production Address",
        help="Customer address for furniture installation or on-site manufacturing.",
        copy=False,
        groups="base.group_user",
    )
    order_attachment = fields.Binary(
        string="Drawing / File Attachment",
        attachment=True,
        copy=False,
        groups="base.group_user",
        help="Upload one drawing, measurement PDF, image, or technical file.",
    )
    attachment_name = fields.Char(
        string="File Name",
        copy=False,
        groups="base.group_user",
    )
