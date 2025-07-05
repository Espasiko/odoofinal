"""
Script para actualizar automáticamente los datos de la compañía principal en Odoo usando XML-RPC.
Compatible con Odoo 16/17/18+ y preparado para ejecutarse dentro o fuera del contenedor Docker.

Configura las variables ODOO_URL, ODOO_DB, ODOO_USER y ODOO_PASSWORD según tu entorno.
"""
import xmlrpc.client

# CONFIGURACIÓN: AJUSTA ESTOS DATOS SEGÚN TU INSTANCIA
ODOO_URL = "http://localhost:8069"  # Cambia el puerto si es necesario
ODOO_DB = "manus_odoo-bd"           # Nombre de la base de datos
ODOO_USER = "yo@mail.com"                 # Usuario admin
ODOO_PASSWORD = "admin"             # Contraseña admin

# NUEVOS DATOS DE LA EMPRESA
NUEVOS_DATOS = {
    'name': "El Pelotazo Electrohogar",
    'street': "Carretera de Alicún, nº 172 - Bajo",
    'zip': "04740",
    'city': "Roquetas de Mar",
    'state_id': False,  # Si quieres especificar provincia, pon el ID aquí
    'country_id': False,  # Si quieres especificar país, pon el ID aquí
    'phone': "622609477",
    'email': "elpelotazo23@gmail.com",
}

def main():
    print("Conectando a Odoo en:", ODOO_URL)
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        print("Error: No se pudo autenticar en Odoo. Verifica usuario, contraseña y base de datos.")
        return
    print("Autenticado con UID:", uid)

    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

    # Buscar la compañía principal
    company_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.company', 'search', [[['id', '=', 1]]]
    )
    if not company_ids:
        print("No se encontró la compañía principal (ID=1)")
        return
    print("ID de compañía principal:", company_ids[0])

    # Actualizar datos
    result = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'res.company', 'write',
        [company_ids, NUEVOS_DATOS]
    )
    if result:
        print("✅ Datos de la empresa actualizados correctamente.")
    else:
        print("❌ Error al actualizar los datos de la empresa.")

if __name__ == "__main__":
    main()
