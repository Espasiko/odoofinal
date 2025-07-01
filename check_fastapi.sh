#!/bin/bash
echo "Verificando estado del contenedor FastAPI..."
docker ps | grep fastapi
echo -e "\nLogs recientes del contenedor FastAPI:"
docker logs --tail 20 fastapi