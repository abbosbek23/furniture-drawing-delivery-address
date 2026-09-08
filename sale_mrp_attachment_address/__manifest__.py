{
    "name": "Sales / Manufacturing Address and Drawing",
    "summary": "Share furniture installation addresses and drawings with manufacturing",
    "version": "19.0.1.0.0",
    "category": "Manufacturing/Manufacturing",
    "author": "Furniture Manufacturing",
    "license": "LGPL-3",
    "depends": ["sale_management", "sale_mrp"],
    "data": [
        "views/sale_order_views.xml",
        "views/mrp_production_views.xml",
    ],
    # Only existing models are extended; no additional model ACLs are needed.
    "installable": True,
    # Listed as an application so it is visible and installable from Apps
    # without clearing the default filter or enabling developer mode.
    "application": True,
    "auto_install": False,
    "images": ["static/description/icon.png"],
}
