#!/bin/bash

# Script de ejecución para el RAG de la Biblioteca Neville Goddard

# Ir al directorio del script
cd "$(dirname "$0")"

# Verificar si existe el entorno virtual
if [ -d ".venv" ]; then
    echo "=========================================================="
    echo "Activando entorno virtual (.venv)..."
    source .venv/bin/activate
else
    echo "Error: No se encontró la carpeta .venv."
    echo "Por favor ejecuta primero la instalación de dependencias."
    exit 1
fi

# Iniciar Uvicorn
echo "=========================================================="
echo "Iniciando el servidor en http://localhost:8000"
echo "Presiona CTRL+C para detener el servidor."
echo "=========================================================="

PYTHONUNBUFFERED=1 python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

