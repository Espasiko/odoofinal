# Configuración Real de Base de Datos PostgreSQL - El Pelotazo

**Fecha de extracción**: 05/06/2025 17:57  
**Fuente**: Extracción directa desde PostgreSQL (NO documentación del proyecto)

## 🔗 INFORMACIÓN DE CONEXIÓN BD

- **Host**: localhost (127.0.0.1)
- **Puerto**: 5432
- **Usuario BD**: odoo
- **Contraseña BD**: odoo

## 🗄️ BASES DE DATOS EXISTENTES

### 1. **el_pelotazo** (21MB)
- **Owner**: odoo
- **Creada**: 2025-05-27 19:09:13
- **UUID**: 13ab0600-3b2e-11f0-b870-00155d47fb23
- **Secret**: e35ffbe1-190e-4bc5-82a7-0d616cd697a7

### 2. **odoo_pelotazo** (73MB)
- **Owner**: odoo
- **Creada**: 2025-05-22 15:58:28
- **UUID**: 99e61aa9-3725-11f0-88d5-00155d47fc94
- **Secret**: 378483d9-ab51-4ecf-a3de-170d7a1fea9d

## 👥 USUARIOS ADMINISTRADORES

### BD: el_pelotazo
1. **admin** (ID: 2)
   - **Nombre**: Mitchell Admin
   - **Email**: admin@yourcompany.example.com
   - **Password Hash**: `$pbkdf2-sha512$600000$qnVOaY3R.h9jTEnJmeEqtqgkyfze.Apg.0dVjyfwzftO5Ady7ndJxezG26Q`

2. **demo** (ID: 6)
   - **Nombre**: Marc Demo
   - **Email**: mark.brown23@example.com
   - **Password Hash**: `$pbkdf2-sha512$600000$I6R0jhECIMSYcy6lNGbMuQ$BmT3XkeVAUXoxW6BGxVaSxfqUnyCrjveVeeoPyTh2zLFrZ/Jd7YI0tIcSLnh3kyUrTQco3b/ZSF9GxykZQGJDw`

3. **portal** (ID: 7)
   - **Nombre**: Joel Willis
   - **Email**: joel.willis63@example.com
   - **Password Hash**: `$pbkdf2-sha512$600000$rxWCkPK.txZiLIVwjvEeAw$rtoc/.K54OmOHJIKnnTK2yQBesCmyuYsFxiQWikkESRO0P7muQxhgQRvFR19P1uzczuqefTECRQTFQvhpowqvA`

### BD: odoo_pelotazo
1. **admin** (ID: 2)
   - **Nombre**: Administrator
   - **Email**: admin@example.com
   - **Password Hash**: `$pbkdf2-sha512$600000$dy6l1JoTwnhPCSHEeI/R2g$I0VjitzOBjXhjs6UxuP8RK4QARGdUBCz96xAj9PWxpDmEw3g5lEQEtFWJpRaGjPGmgMoKfqA.A3sGgganaVnng`

## 🏢 EMPRESAS CONFIGURADAS

### BD: el_pelotazo
- **My Company (Chicago)**: chicago@yourcompany.com, +1 312 349 3030
- **YourCompany**: info@yourcompany.com, +1 555-555-5556

### BD: odoo_pelotazo
- **El Pelotazo Electrodomésticos**: info@elpelotazo.com, +34 912 345 678

## 🔧 MÓDULOS INSTALADOS (79 total)

Los principales módulos instalados incluyen:
- **account** - Contabilidad
- **sale** - Ventas
- **purchase** - Compras
- **stock** - Inventario
- **website** - Sitio web
- **website_sale** - Tienda online
- **payment** - Pagos
- **delivery** - Envíos
- **portal** - Portal de clientes
- **mail** - Correo electrónico
- Y 69 módulos adicionales...

## 💾 BACKUPS

### Backups Creados Hoy (05/06/2025)
- `/home/espasiko/backups_20250605_175257/el_pelotazo_backup_20250605_175257.sql` (21MB)
- `/home/espasiko/backups_20250605_175310/odoo_pelotazo_backup_20250605_175310.sql` (73MB)

### Backups Existentes
- `/home/espasiko/mainmanusodoo/manusodoo-main/backups/` (28 mayo 2025)
- `/home/espasiko/mainmanusodoo/manusodoo-roto/backups/` (28 mayo 2025)

## ⚠️ NOTAS IMPORTANTES

1. **Contraseñas**: Todas las contraseñas están hasheadas con PBKDF2-SHA512, no en texto plano.
2. **Configuración Real vs Documentación**: Esta información fue extraída directamente de PostgreSQL y puede diferir de la documentación del proyecto.
3. **Puertos Activos**: 
   - PostgreSQL: 5432
   - Odoo: 8070, 8080
   - FastAPI: 8000
4. **Base de Datos Principal**: `odoo_pelotazo` parece ser la BD principal con "El Pelotazo Electrodomésticos"

## 🔐 CREDENCIALES DE ACCESO RÁPIDO

```bash
# Conexión PostgreSQL
PGPASSWORD=odoo psql -h localhost -p 5432 -U odoo -d odoo_pelotazo

# URLs de acceso
http://localhost:8070/shop  # Tienda Odoo
http://localhost:8080       # Odoo Backend
http://localhost:8000       # FastAPI Backend
```

---
*Documento generado automáticamente el 05/06/2025 mediante extracción directa desde PostgreSQL*
