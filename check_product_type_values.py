import xmlrpc.client

# Odoo connection details
url = "http://localhost:8069"
db = "manus_odoo-bd"
username = "yo@mail.com"
password = "admin"

try:
    print("Connecting to Odoo...")
    # Connect to Odoo
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    
    # Get the fields of product.template
    fields = models.execute_kw(
        db, uid, password,
        'product.template', 'fields_get',
        [], {'attributes': ['string', 'type', 'selection']}
    )
    
    # Print information about the 'type' field
    if 'type' in fields:
        print("\nInformation about 'type' field in product.template:")
        print(f"Type: {fields['type']['type']}")
        print(f"Label: {fields['type']['string']}")
        
        if 'selection' in fields['type']:
            print("\nValid values for 'type' field:")
            for value, label in fields['type']['selection']:
                print(f"- {value}: {label}")
    
    # Get some example products with their types
    print("\nExample products and their types:")
    products = models.execute_kw(
        db, uid, password,
        'product.template', 'search_read',
        [[], ['name', 'type']],
        {'limit': 10}
    )
    
    for p in products:
        print(f"- {p['name']}: {p.get('type')}")
        
except Exception as e:
    print(f"Error: {str(e)}")
