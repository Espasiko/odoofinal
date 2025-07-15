#!/bin/bash
echo "Reiniciando servicio FastAPI..."
docker restart fastapi
echo "Esperando a que el servicio esté disponible..."
sleep 5
echo "Verificando logs del servicio..."
docker logs --tail 20 fastapi
echo "Servicio FastAPI reiniciado."
echo "Puedes probar el servicio con: curl -X POST http://localhost:8000/token -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=yo@mail.com&password=admin'"
