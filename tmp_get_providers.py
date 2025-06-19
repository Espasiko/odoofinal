from api.services.odoo_service import OdooService

svc = OdooService()
providers = svc.get_providers()
print(f"Proveedores encontrados: {len(providers)}")
for p in providers:
    print(f"{p.id} - {p.name} - {p.email}")