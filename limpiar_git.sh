#!/bin/bash
# Script para eliminar archivos grandes del índice de Git sin borrarlos del disco

# Eliminar archivos PDF
find . -name "*.pdf" | grep -v "node_modules" | xargs -I{} git rm --cached "{}"

# Eliminar archivos de imágenes grandes
find . -name "*.gif" | grep -v "node_modules" | xargs -I{} git rm --cached "{}"
find . -name "*.png" | grep -v "node_modules" | xargs -I{} git rm --cached "{}"
find . -name "*.jpg" | grep -v "node_modules" | xargs -I{} git rm --cached "{}"

# Eliminar archivos JSON grandes
find . -name "*.json" | grep -v "node_modules" | grep -v "package.json" | grep -v "tsconfig.json" | xargs -I{} git rm --cached "{}"

# Eliminar archivos ZIP
find . -name "*.zip" | xargs -I{} git rm --cached "{}"

# Eliminar carpetas específicas del índice de Git
git rm --cached -r data_test/filestore/ 2>/dev/null || true
git rm --cached -r informes/ 2>/dev/null || true
git rm --cached -r ejemplos/ 2>/dev/null || true
git rm --cached -r addons_backup/ 2>/dev/null || true
git rm --cached -r n8n/flujos/ 2>/dev/null || true

echo "Limpieza completada. Los archivos siguen en el disco pero ya no están siendo rastreados por Git."
