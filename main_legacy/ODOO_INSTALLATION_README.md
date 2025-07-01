# Odoo 18 Installation Guide

## Installation Complete! 🎉

Odoo 18 has been successfully installed and is running in Docker containers.

## Access Information

- **Odoo Web Interface**: http://localhost:8069
- **Database**: PostgreSQL running on port 5433
- **Default Admin Password**: admin

## Container Management

### Check Container Status
```bash
sudo docker ps
```

### View Logs
```bash
# Odoo logs
sudo docker logs odoo-app

# Database logs
sudo docker logs odoo-db
```

### Stop Containers
```bash
sudo docker stop odoo-app odoo-db
```

### Start Containers
```bash
sudo docker start odoo-db
sudo docker start odoo-app
```

### Remove Containers (if needed)
```bash
sudo docker stop odoo-app odoo-db
sudo docker rm odoo-app odoo-db
```

## Configuration

- **Odoo Configuration**: `./config/odoo.conf`
- **Custom Addons**: Place in `./addons/` directory
- **Database Connection**: 
  - Host: db (internal) / localhost:5433 (external)
  - User: odoo
  - Password: odoo
  - Database: postgres

## First Setup

1. Open http://localhost:8069 in your browser
2. Create a new database or use the existing one
3. Set up your admin user
4. Start configuring your Odoo instance

## Troubleshooting

### If containers don't start:
```bash
# Check if ports are available
ss -tlnp | grep :8069
ss -tlnp | grep :5433

# Restart Docker service
sudo systemctl restart docker
```

### If you need to reset everything:
```bash
sudo docker stop odoo-app odoo-db
sudo docker rm odoo-app odoo-db
sudo docker volume prune
```

Then run the installation commands again.

## Security Notes

- Change default passwords in production
- Configure firewall rules appropriately
- Use SSL/TLS for production deployments
- Regular backups of database and filestore