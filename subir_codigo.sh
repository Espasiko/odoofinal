#!/bin/bash
# Script para subir el código actual al repositorio

echo "=== Añadiendo la plantilla Excel y .gitignore al repositorio ==="
git add ejemplos/plantillas/
git add .gitignore

echo -e "\n=== Creando commit ==="
git commit -m "Añadida plantilla Excel para importación y actualizado .gitignore"

echo -e "\n=== Verificando rama actual ==="
rama_actual=$(git branch --show-current)
echo "Rama actual: $rama_actual"

echo -e "\n=== Verificando si existe la rama version-consolidada-13-07 ==="
if git show-ref --verify --quiet refs/heads/version-consolidada-13-07; then
    echo "La rama version-consolidada-13-07 existe."
    echo "Cambiando a la rama version-consolidada-13-07..."
    git checkout version-consolidada-13-07
    echo "Fusionando cambios desde $rama_actual..."
    git merge $rama_actual
else
    echo "La rama version-consolidada-13-07 no existe."
    echo "Creando y cambiando a la rama version-consolidada-13-07..."
    git checkout -b version-consolidada-13-07
fi

echo -e "\n=== Subiendo cambios al repositorio remoto ==="
git push origin version-consolidada-13-07

echo -e "\n=== Proceso completado ==="
echo "Los cambios han sido subidos a la rama version-consolidada-13-07"