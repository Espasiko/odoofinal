#!/bin/bash
echo "Reiniciando contenedor FastAPI..."
docker-compose restart fastapi
sleep 5
echo -e "\nEstado del contenedor FastAPI:"
docker ps | grep fastapi
echo -e "\nLogs recientes del contenedor FastAPI:"
docker logs --tail 30 fastapi