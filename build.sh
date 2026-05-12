#!/usr/bin/env bash
set -o errexit

echo ">>> Instalando dependencias..."
pip install -r requirements.txt

echo ">>> Ejecutando migraciones..."
python manage.py migrate --noinput

echo ">>> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo ">>> Build completado exitosamente"