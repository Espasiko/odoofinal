{
    'name': 'Pelotazo Extended',
    'version': '1.0',
    'category': 'Sales/Inventory',
    'summary': 'Módulo para extender la funcionalidad de Pelotazo con gestión de inventario y OCR.',
    'description': """
        Este módulo extiende las funcionalidades de Odoo para el proyecto El Pelotazo,
        incluyendo campos personalizados para productos, integración con OCR para facturas,
        y mejoras en la gestión de inventario.
    """,
    'author': 'Manus AI',
    'website': 'https://www.odoo.com',
    'depends': ['base', 'product', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/account_invoice_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

