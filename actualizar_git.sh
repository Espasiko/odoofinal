#!/bin/bash
# Script creado el 17/07/2025 para actualizar el repositorio Git
# Script para actualizar el repositorio Git

# Mostrar el estado actual
echo "Estado actual del repositorio:"
git status

# Añadir la carpeta de ejemplos/plantillas al repositorio
echo -e "\nAñadiendo la carpeta de plantillas al repositorio:"
git add ejemplos/plantillas/

# Verificar si hay cambios en main.py
echo -e "\nVerificando cambios en main.py:"
git add main.py

# Verificar si hay cambios en .gitignore
echo -e "\nVerificando cambios en .gitignore:"
git add .gitignore

# Mostrar los archivos que se van a incluir en el commit
echo -e "\nArchivos que se van a incluir en el commit:"
git status

# Preguntar antes de hacer commit
echo -e "\n¡ATENCIÓN! Se van a hacer cambios en el repositorio."
echo "¿Deseas continuar con el commit? (s/n)"
read respuesta

if [ "$respuesta" = "s" ]; then
    # Hacer commit
    git commit -m "Añadida plantilla Excel para importación y actualizado .gitignore"
    
    # Verificar la rama actual
    rama_actual=$(git branch --show-current)
    echo -e "\nRama actual: $rama_actual"
    
    # Verificar si existe la rama version-consolidada-13-07
    if git show-ref --verify --quiet refs/heads/version-consolidada-13-07; then
        echo "La rama version-consolidada-13-07 existe."
        
        # Preguntar si quiere cambiar a esa rama
        echo "¿Deseas cambiar a la rama version-consolidada-13-07? (s/n)"
        read cambiar_rama
        
        if [ "$cambiar_rama" = "s" ]; then
            git checkout version-consolidada-13-07
            git merge $rama_actual
            echo "Cambios fusionados a la rama version-consolidada-13-07"
        else
            echo "Permaneciendo en la rama $rama_actual"
        fi
    else
        echo "La rama version-consolidada-13-07 no existe."
        echo "¿Deseas crear la rama version-consolidada-13-07? (s/n)"
        read crear_rama
        
        if [ "$crear_rama" = "s" ]; then
            git checkout -b version-consolidada-13-07
            echo "Rama version-consolidada-13-07 creada y seleccionada"
        else
            echo "Permaneciendo en la rama $rama_actual"
        fi
    fi
    
    # Preguntar si quiere hacer push
    echo "¿Deseas hacer push de los cambios? (s/n)"
    read hacer_push
    
    if [ "$hacer_push" = "s" ]; then
        rama_actual=$(git branch --show-current)
        git push origin $rama_actual
        echo "Cambios subidos a la rama $rama_actual"
    else
        echo "No se ha hecho push de los cambios"
    fi
else
    echo "Operación cancelada. No se ha hecho commit."
fi