#!/usr/bin/env python
"""
Script para crear datos de prueba para el sistema de colegio
Ejecutar con: python manage.py shell < crear_datos_prueba.py
"""

import os
import django
from datetime import date, datetime, timedelta
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'colegio.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import (
    Colegio, Curso, Materia, Maestro, Alumno, Padre, 
    Nota, Asistencia, Participacion
)

def crear_datos_prueba():
    print("Creando datos de prueba...")
    
    # Crear superusuario
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@colegio.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        print("✓ Superusuario creado: admin/admin123")
    
    # Crear colegio
    colegio, created = Colegio.objects.get_or_create(
        nombre="Colegio San José",
        defaults={
            'direccion': "Av. Siempre Viva 123, La Paz",
            'latitud': -16.5000,
            'longitud': -68.1193,
        }
    )
    if created:
        print(f"✓ Colegio creado: {colegio.nombre}")
    
    # Crear maestros
    maestros_data = [
        {'username': 'maestro1', 'password': 'maestro123', 'first_name': 'María', 'last_name': 'García', 'telefono': '70123456'},
        {'username': 'maestro2', 'password': 'maestro123', 'first_name': 'Juan', 'last_name': 'Pérez', 'telefono': '70234567'},
        {'username': 'maestro3', 'password': 'maestro123', 'first_name': 'Ana', 'last_name': 'López', 'telefono': '70345678'},
    ]
    
    maestros = []
    for data in maestros_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': f"{data['username']}@colegio.com"
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
        
        maestro, created = Maestro.objects.get_or_create(
            user=user,
            defaults={'telefono': data['telefono']}
        )
        maestros.append(maestro)
        if created:
            print(f"✓ Maestro creado: {data['username']}/maestro123")
    
    # Crear cursos
    cursos_data = [
        {'nombre': '1ro A', 'tutor': maestros[0]},
        {'nombre': '2do A', 'tutor': maestros[1]},
        {'nombre': '3ro A', 'tutor': maestros[2]},
    ]
    
    cursos = []
    for data in cursos_data:
        curso, created = Curso.objects.get_or_create(
            nombre=data['nombre'],
            colegio=colegio,
            defaults={'tutor': data['tutor']}
        )
        cursos.append(curso)
        if created:
            print(f"✓ Curso creado: {data['nombre']}")
    
    # Crear materias para cada curso
    materias_base = ['Matemáticas', 'Lenguaje', 'Ciencias Naturales', 'Ciencias Sociales', 'Educación Física']
    
    for curso in cursos:
        for materia_nombre in materias_base:
            materia, created = Materia.objects.get_or_create(
                nombre=materia_nombre,
                curso=curso,
                defaults={'descripcion': f"{materia_nombre} para {curso.nombre}"}
            )
            if created:
                print(f"✓ Materia creada: {materia_nombre} - {curso.nombre}")
    
    # Crear padres
    padres_data = [
        {'username': 'padre1', 'password': 'padre123', 'first_name': 'Carlos', 'last_name': 'Rodríguez', 'telefono': '60123456'},
        {'username': 'padre2', 'password': 'padre123', 'first_name': 'Laura', 'last_name': 'Martínez', 'telefono': '60234567'},
        {'username': 'padre3', 'password': 'padre123', 'first_name': 'Pedro', 'last_name': 'Sánchez', 'telefono': '60345678'},
        {'username': 'padre4', 'password': 'padre123', 'first_name': 'Carmen', 'last_name': 'Flores', 'telefono': '60456789'},
    ]
    
    padres = []
    for data in padres_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': f"{data['username']}@gmail.com"
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
        
        padre, created = Padre.objects.get_or_create(
            user=user,
            defaults={'telefono': data['telefono']}
        )
        padres.append(padre)
        if created:
            print(f"✓ Padre creado: {data['username']}/padre123")
    
    # Crear alumnos
    alumnos_data = [
        {'username': 'alumno1', 'password': 'alumno123', 'first_name': 'Miguel', 'last_name': 'Rodríguez', 'curso': cursos[0], 'padre': padres[0]},
        {'username': 'alumno2', 'password': 'alumno123', 'first_name': 'Sofia', 'last_name': 'Martínez', 'curso': cursos[0], 'padre': padres[1]},
        {'username': 'alumno3', 'password': 'alumno123', 'first_name': 'Diego', 'last_name': 'Sánchez', 'curso': cursos[1], 'padre': padres[2]},
        {'username': 'alumno4', 'password': 'alumno123', 'first_name': 'Valentina', 'last_name': 'Flores', 'curso': cursos[1], 'padre': padres[3]},
        {'username': 'alumno5', 'password': 'alumno123', 'first_name': 'Sebastián', 'last_name': 'Vargas', 'curso': cursos[2], 'padre': padres[0]},
        {'username': 'alumno6', 'password': 'alumno123', 'first_name': 'Isabella', 'last_name': 'Morales', 'curso': cursos[2], 'padre': padres[1]},
    ]
    
    alumnos = []
    for data in alumnos_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': f"{data['username']}@estudiante.com",
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
        
        alumno, created = Alumno.objects.get_or_create(
            user=user,
            defaults={
                'curso': data['curso'],
                'fecha_nacimiento': date(2010, random.randint(1, 12), random.randint(1, 28))
            }
        )
        if created:
            alumno.padres.add(data['padre'])
        alumnos.append(alumno)
        if created:
            print(f"✓ Alumno creado: {data['username']}/alumno123")
    
    # Crear notas de ejemplo
    periodos = ['2024-T1', '2024-T2', '2024-T3']
    
    for alumno in alumnos:
        materias_curso = Materia.objects.filter(curso=alumno.curso)
        for periodo in periodos:
            for materia in materias_curso:
                nota_valor = random.uniform(60, 95)  # Notas entre 60 y 95
                nota, created = Nota.objects.get_or_create(
                    alumno=alumno,
                    materia=materia,
                    periodo=periodo,
                    defaults={'valor': round(nota_valor, 1)}
                )
                if created:
                    print(f"✓ Nota creada: {alumno.user.username} - {materia.nombre} - {periodo}: {nota.valor}")
    
    # Crear asistencias de ejemplo (últimos 30 días)
    for alumno in alumnos:
        for i in range(30):
            fecha = date.today() - timedelta(days=i)
            # 85% de probabilidad de asistir
            presente = random.random() < 0.85
            asistencia, created = Asistencia.objects.get_or_create(
                alumno=alumno,
                fecha=fecha,
                defaults={
                    'presente': presente,
                    'registrado_por_qr': random.random() < 0.7  # 70% por QR
                }
            )
    
    print("✓ Asistencias creadas para los últimos 30 días")
    
    # Crear participaciones de ejemplo
    for alumno in alumnos:
        materias_curso = Materia.objects.filter(curso=alumno.curso)
        for i in range(20):  # 20 participaciones por alumno
            fecha = date.today() - timedelta(days=random.randint(1, 60))
            materia = random.choice(materias_curso)
            valor = random.uniform(2, 5)  # Participaciones entre 2 y 5
            
            participacion, created = Participacion.objects.get_or_create(
                alumno=alumno,
                materia=materia,
                fecha=fecha,
                defaults={
                    'valor': round(valor, 1),
                    'observaciones': f"Participación en {materia.nombre}"
                }
            )
    
    print("✓ Participaciones creadas")
    
    print("\n=== DATOS DE PRUEBA CREADOS EXITOSAMENTE ===")
    print("\nUsuarios creados:")
    print("- Admin: admin/admin123")
    print("- Maestros: maestro1, maestro2, maestro3 / maestro123")
    print("- Alumnos: alumno1, alumno2, alumno3, alumno4, alumno5, alumno6 / alumno123")
    print("- Padres: padre1, padre2, padre3, padre4 / padre123")
    print(f"\nToken QR del colegio: {colegio.token_qr}")
    print("Ubicación del colegio: -16.5000, -68.1193")

if __name__ == "__main__":
    crear_datos_prueba() 