
import sys
import asyncio
sys.path.append('.')
from odoo.client import OdooClient
from config import config

async def test_connection():
    try:
        client = OdooClient(
            url=config.odoo.url,
            database=config.odoo.database,
            username=config.odoo.username,
            password=config.odoo.password
        )
        await client.connect()
        version = await client.get_server_version()
        print(f"✓ Conectado a Odoo versión: {version}")
        await client.disconnect()
    except Exception as e:
        print(f"❌ Error conectando a Odoo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
