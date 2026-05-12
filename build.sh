#!/usr/bin/env bash
# Salir en caso de error
set -o errexit

echo ">> Instalando dependencias..."
pip install -r requirements.txt

echo ">> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo ">> Creando tablas en la base de datos (--run-syncdb)..."
# Este es el comando clave para crear las tablas desde cero.
python manage.py migrate --run-syncdb

echo ">> Aplicando migraciones pendientes..."
python manage.py migrate

echo ">> Creando superusuario si no existe..."
# Este comando intenta crear un superusuario solo si no existe uno.
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(is_superuser=True).exists() or User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')" | python manage.py shell

echo ">> ¡Build finalizado!"