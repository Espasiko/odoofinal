#!/bin/bash
# Script para verificar archivos nuevos en el proyecto

echo "Archivos nuevos que no están siendo rastreados por Git:"
git ls-files --others --exclude-standard

echo -e "\nArchivos modificados:"
git diff --name-only

echo -e "\nEstado del repositorio:"
git status