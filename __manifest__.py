{
    'name': 'Reports Design',
    'version': '1.0',
    'summary': 'Custom PDF Report Layouts',
    'category': 'Tools',
    'author': 'DSM',
    'depends': ['base', 'web', 'sale','bi_sale_purchase_discount_with_tax'],  # Add 'account' if invoice reports
    'data': [
        'report/templates.xml',
    ],
    'installable': True,
    'application': False,
}
