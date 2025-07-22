@echo off
echo =====================================
echo   Sistema de Informacion del Colegio
echo         Instalacion Automatica
echo =====================================
echo.

echo [1/6] Activando entorno virtual...
call venv\Scripts\activate

echo [2/6] Instalando dependencias...
pip install -r requirements.txt

echo [3/6] Aplicando migraciones...
python manage.py migrate

echo [4/6] Creando datos de prueba...
python crear_datos_prueba.py

echo [5/6] Creando superusuario admin (si no existe)...
echo from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@colegio.com', 'admin123') | python manage.py shell

echo [6/6] Iniciando servidor...
echo.
echo =====================================
echo    INSTALACION COMPLETADA
echo =====================================
echo.
echo Usuarios de prueba creados:
echo - Admin: admin / admin123
echo - Maestros: maestro1, maestro2, maestro3 / maestro123  
echo - Alumnos: alumno1-6 / alumno123
echo - Padres: padre1-4 / padre123
echo.
echo El servidor se iniciara en: http://localhost:8000
echo Panel de admin en: http://localhost:8000/admin
echo API Root en: http://localhost:8000/api
echo.
echo Presiona Ctrl+C para detener el servidor
echo =====================================
echo.

python manage.py runserver 