import xmlrpc.client
import re

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Diccionario de categorías basado en palabras clave
category_keywords = {
    'Lavadoras': ['lavadora', 'washer'],
    'Frigoríficos': ['frigorifico', 'fridge', 'refrigerador'],
    'Microondas': ['microonda', 'microwave'],
    'Hornos': ['horno', 'oven'],
    'Aires Acondicionados': ['aire acondicionado', 'air conditioner', 'calefactor', 'radiador'],
    'Batidoras': ['batidora', 'blender'],
    'Cafeteras': ['cafetera', 'coffee maker'],
    'Aspiradoras': ['aspiradora', 'vacuum'],
    'Placas': ['placa', 'cooktop', 'induccion'],
    'Televisores': ['televisor', 'tv', 'television'],
    'Lavavajillas': ['lavavajilla', 'dishwasher'],
    'Secadoras': ['secadora', 'dryer'],
    'Freidoras': ['freidora', 'airfryer', 'fryer'],
    'Pequeños Electrodomésticos': ['plancha', 'tostadora', 'licuadora', 'sandwichera', 'grill', 'extractor', 'ventilador'],
    'Otros Electrodomésticos': []  # Default si no coincide con nada específico
}

# Lista de marcas conocidas para etiquetas
known_brands = ['rowenta', 'cecotec', 'lg', 'samsung', 'bosch', 'teka', 'balay', 'siemens', 'aeg', 'electrolux', 'whirlpool', 'miele', 'haier', 'beko', 'candy', 'hoover', 'panasonic', 'philips', 'sony', 'sharp', 'tcl', 'hisense', 'grundig', 'ufesa', 'orbegozo', 'jata', 'beken', 'eas', 'electrodomesticos', 'nevir', 'vitrokitchen']

# Obtener todas las categorías existentes
categories = models.execute_kw(db, uid, password, 'product.category', 'search_read', [[]], {'fields': ['id', 'name']})
category_map = {cat['name']: cat['id'] for cat in categories}

# Obtener productos en categoría 'All' (ID: 1)
all_products = models.execute_kw(db, uid, password, 'product.template', 'search_read', 
                                [[['categ_id', '=', 1]]], 
                                {'fields': ['id', 'name', 'default_code']})

print(f'Total de productos en categoría "All": {len(all_products)}')

# Contadores
reassigned_count = 0
brand_tags_added = 0

# Procesar cada producto
for product in all_products:
    prod_id = product['id']
    prod_name = product['name'].lower()
    reassigned = False
    
    # Intentar asignar categoría basada en palabras clave
    for cat_name, keywords in category_keywords.items():
        if any(keyword in prod_name for keyword in keywords):
            if cat_name in category_map:
                models.execute_kw(db, uid, password, 'product.template', 'write', [[prod_id], {'categ_id': category_map[cat_name]}])
                reassigned_count += 1
                reassigned = True
                print(f'Reasignado "{product["name"]}" a categoría "{cat_name}"')
                break
    
    # Si no se reasignó, asignar a 'Otros Electrodomésticos' si existe
    if not reassigned and 'Otros Electrodomésticos' in category_map:
        models.execute_kw(db, uid, password, 'product.template', 'write', [[prod_id], {'categ_id': category_map['Otros Electrodomésticos']}])
        reassigned_count += 1
        print(f'Reasignado "{product["name"]}" a categoría "Otros Electrodomésticos" por defecto')
    elif not reassigned:
        print(f'No se pudo reasignar "{product["name"]}", permanece en "All"')
    
    # Detectar y asignar etiquetas de marca
    for brand in known_brands:
        if brand in prod_name:
            tag_id = models.execute_kw(db, uid, password, 'product.tag', 'search', [[['name', '=', brand.capitalize()]]])
            if not tag_id:
                tag_id = models.execute_kw(db, uid, password, 'product.tag', 'create', [{'name': brand.capitalize()}])
                print(f'Creada etiqueta de marca "{brand.capitalize()}"')
            else:
                tag_id = tag_id[0]
            models.execute_kw(db, uid, password, 'product.template', 'write', [[prod_id], {'product_tag_ids': [(4, tag_id)]}])
            brand_tags_added += 1
            print(f'Añadida etiqueta "{brand.capitalize()}" a "{product["name"]}"')
            break

print(f'Resumen: {reassigned_count} productos reasignados de categoría, {brand_tags_added} etiquetas de marca añadidas')
