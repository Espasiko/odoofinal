import xmlrpc.client

# Odoo connection details
url = "http://localhost:8069"
db = "manus_odoo-bd"
username = "yo@mail.com"
password = "admin"

def update_product(product_id, product_name, new_type):
    try:
        print(f"Updating product: {product_name} (ID: {product_id}) to type '{new_type}'")
        
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        
        # Update product type
        result = models.execute_kw(
            db, uid, password,
            'product.template', 'write',
            [[product_id], {'type': new_type}]
        )
        
        # Verify the update
        updated_product = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [[product_id], ['name', 'type']]
        )
        
        if updated_product and updated_product[0]['type'] == new_type:
            print(f"✅ Successfully updated product: {product_name} (ID: {product_id}) to type '{new_type}'")
            return True
        else:
            print(f"❌ Failed to update product: {product_name} (ID: {product_id})")
            return False
            
    except Exception as e:
        print(f"❌ Error updating product {product_name} (ID: {product_id}): {str(e)}")
        return False

def main():
    # Product to update: ID, Name, New Type
    product_to_update = (225, "1 SARTEN POLKA 18 (NEGRO MANGO TURQUESA)", "consu")
    
    print("Starting product type correction...\n")
    
    success = update_product(*product_to_update)
    
    if success:
        print("\n✅ Product type correction completed successfully!")
    else:
        print("\n❌ There were errors during the update. Please check the messages above.")

if __name__ == "__main__":
    main()
