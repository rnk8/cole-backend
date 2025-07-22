#!/usr/bin/env python
"""
Script MASIVO para crear datos de prueba del Sistema de Información del Colegio
Genera un colegio completo con todos los niveles educativos y datos realistas
Ejecutar con: python crear_datos_masivos.py
"""

import os
import django
from datetime import date, datetime, timedelta
import random
import string
from faker import Faker

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'colegio.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import (
    Colegio, Curso, Materia, Maestro, Alumno, Padre, 
    Nota, Asistencia, Participacion
)

fake = Faker('es_ES')  # Datos en español

# Configuración de datos masivos
CONFIG = {
    'maestros': 50,           # 50 maestros
    'cursos_por_nivel': {     # Estructura realista de cursos
        'Inicial': ['Inicial 3', 'Inicial 4', 'Inicial 5'],
        'Primaria': [f'Primaria {i}°' for i in range(1, 7)],
        'Secundaria': [f'Secundaria {i}°' for i in range(1, 7)]
    },
    'secciones': ['A', 'B', 'C'],  # 3 secciones por curso
    'alumnos_por_seccion': (15, 25),  # Entre 15-25 alumnos por sección
    'materias_por_nivel': {
        'Inicial': ['Desarrollo Cognitivo', 'Desarrollo Motor', 'Desarrollo Social', 'Expresión Artística', 'Música'],
        'Primaria': ['Matemáticas', 'Lenguaje', 'Ciencias Naturales', 'Estudios Sociales', 'Educación Física', 'Arte', 'Música', 'Inglés'],
        'Secundaria': ['Matemáticas', 'Física', 'Química', 'Biología', 'Historia', 'Geografía', 'Literatura', 'Filosofía', 'Inglés', 'Educación Física', 'Arte', 'Informática']
    },
    'periodos': ['2024-T1', '2024-T2', '2024-T3', '2024-T4'],
    'notas_por_periodo': 0.8,  # 80% de alumnos tienen notas por periodo
    'asistencia_dias': 90,     # 90 días de asistencia por trimestre
    'participaciones_por_mes': (2, 8),  # Entre 2-8 participaciones por mes por alumno
}

def generar_username(nombre, apellido, tipo=''):
    """Genera un username único basado en nombre y apellido"""
    base = f"{nombre.lower()}.{apellido.lower().split()[0]}"
    if tipo:
        base = f"{tipo}.{base}"
    
    # Remover caracteres especiales
    base = ''.join(c for c in base if c.isalnum() or c in '._')
    
    # Asegurar unicidad
    counter = 1
    username = base
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1
    
    return username

def crear_superusuario():
    """Crear superusuario si no existe"""
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@colegio.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        print("✓ Superusuario creado: admin/admin123")
        return admin_user
    else:
        print("✓ Superusuario ya existe")
        return User.objects.get(username='admin')

def crear_colegio():
    """Crear el colegio principal"""
    colegio, created = Colegio.objects.get_or_create(
        nombre="Unidad Educativa San José",
        defaults={
            'direccion': "Av. 6 de Agosto #2845, Zona San Pedro, La Paz",
            'latitud': -16.5000,
            'longitud': -68.1193,
            'token_qr': 'QR_COLEGIO_SAN_JOSE_2024'
        }
    )
    if created:
        print(f"✓ Colegio creado: {colegio.nombre}")
    else:
        print(f"✓ Colegio ya existe: {colegio.nombre}")
    return colegio

def crear_maestros():
    """Crear maestros masivamente"""
    print(f"\n📚 Creando {CONFIG['maestros']} maestros...")
    maestros = []
    
    especialidades = [
        'Matemáticas', 'Física', 'Química', 'Biología', 'Historia', 'Geografía',
        'Literatura', 'Filosofía', 'Inglés', 'Educación Física', 'Arte', 
        'Música', 'Informática', 'Psicología', 'Pedagogía', 'Educación Inicial'
    ]
    
    for i in range(CONFIG['maestros']):
        # Generar datos del maestro
        nombre = fake.first_name()
        apellido = fake.last_name()
        username = generar_username(nombre, apellido, 'prof')
        email = f"{username}@colegio.edu.bo"
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password='maestro123',
            first_name=nombre,
            last_name=apellido
        )
        
        # Crear maestro
        maestro = Maestro.objects.create(
            user=user,
            telefono=f"7{random.randint(1000000, 9999999)}",
            especialidad=random.choice(especialidades),
            grado_academico=random.choice(['Licenciatura', 'Maestría', 'Doctorado']),
            años_experiencia=random.randint(1, 25),
            fecha_ingreso=fake.date_between(start_date='-10y', end_date='today')
        )
        
        maestros.append(maestro)
        
        if (i + 1) % 10 == 0:
            print(f"  ✓ Creados {i + 1} maestros...")
    
    print(f"✓ {len(maestros)} maestros creados exitosamente")
    return maestros

def crear_cursos_y_materias(colegio, maestros):
    """Crear cursos y materias de forma masiva"""
    print(f"\n🏫 Creando cursos y materias...")
    cursos = []
    materias = []
    
    maestros_disponibles = maestros.copy()
    random.shuffle(maestros_disponibles)
    maestro_index = 0
    
    for nivel, cursos_nivel in CONFIG['cursos_por_nivel'].items():
        print(f"  📖 Creando cursos de {nivel}...")
        
        for curso_nombre in cursos_nivel:
            for seccion in CONFIG['secciones']:
                nombre_completo = f"{curso_nombre} - Sección {seccion}"
                
                # Asignar tutor
                tutor = maestros_disponibles[maestro_index % len(maestros_disponibles)]
                maestro_index += 1
                
                # Crear curso
                curso = Curso.objects.create(
                    nombre=nombre_completo,
                    nivel=nivel,
                    seccion=seccion,
                    año_academico=2024,
                    capacidad_maxima=random.randint(20, 30),
                    colegio=colegio,
                    tutor=tutor
                )
                cursos.append(curso)
                
                # Crear materias para este curso
                materias_nivel = CONFIG['materias_por_nivel'][nivel]
                for materia_nombre in materias_nivel:
                    # Asignar maestro especialista (puede ser diferente al tutor)
                    maestro_materia = random.choice(maestros)
                    
                    materia = Materia.objects.create(
                        nombre=materia_nombre,
                        curso=curso,
                        maestro=maestro_materia,
                        horas_semanales=random.randint(2, 6),
                        descripcion=f"Materia de {materia_nombre} para {curso.nombre}",
                        codigo=f"{curso.id}-{materia_nombre[:3].upper()}"
                    )
                    materias.append(materia)
    
    print(f"✓ {len(cursos)} cursos creados")
    print(f"✓ {len(materias)} materias creadas")
    return cursos, materias

def crear_padres():
    """Crear padres de familia"""
    print(f"\n👨‍👩‍👧‍👦 Creando padres de familia...")
    padres = []
    
    # Crear familias (parejas de padres)
    num_familias = random.randint(200, 300)
    
    for i in range(num_familias):
        # Crear padre
        nombre_padre = fake.first_name_male()
        apellido_familia = fake.last_name()
        username_padre = generar_username(nombre_padre, apellido_familia, 'padre')
        
        user_padre = User.objects.create_user(
            username=username_padre,
            email=f"{username_padre}@gmail.com",
            password='padre123',
            first_name=nombre_padre,
            last_name=apellido_familia
        )
        
        padre = Padre.objects.create(
            user=user_padre,
            telefono=f"7{random.randint(1000000, 9999999)}",
            ci=f"{random.randint(1000000, 9999999)}",
            ocupacion=fake.job(),
            direccion=fake.address()
        )
        padres.append(padre)
        
        # Crear madre (80% de probabilidad)
        if random.random() < 0.8:
            nombre_madre = fake.first_name_female()
            username_madre = generar_username(nombre_madre, apellido_familia, 'madre')
            
            user_madre = User.objects.create_user(
                username=username_madre,
                email=f"{username_madre}@gmail.com",
                password='padre123',
                first_name=nombre_madre,
                last_name=apellido_familia
            )
            
            madre = Padre.objects.create(
                user=user_madre,
                telefono=f"7{random.randint(1000000, 9999999)}",
                ci=f"{random.randint(1000000, 9999999)}",
                ocupacion=fake.job(),
                direccion=padre.direccion  # Misma dirección familiar
            )
            padres.append(madre)
        
        if (i + 1) % 50 == 0:
            print(f"  ✓ Creadas {i + 1} familias...")
    
    print(f"✓ {len(padres)} padres creados")
    return padres

def crear_alumnos(cursos, padres):
    """Crear alumnos masivamente"""
    print(f"\n👨‍🎓 Creando alumnos para todos los cursos...")
    alumnos = []
    padres_disponibles = padres.copy()
    
    for curso in cursos:
        # Determinar número de alumnos para este curso
        num_alumnos = random.randint(*CONFIG['alumnos_por_seccion'])
        
        print(f"  📝 Creando {num_alumnos} alumnos para {curso.nombre}...")
        
        for i in range(num_alumnos):
            # Generar datos del alumno
            nombre = fake.first_name()
            apellido = fake.last_name()
            username = generar_username(nombre, apellido, 'est')
            
            # Calcular edad según el nivel
            if 'Inicial' in curso.nombre:
                edad = random.randint(3, 5)
            elif 'Primaria' in curso.nombre:
                grado = int(curso.nombre.split()[1][0])
                edad = 5 + grado
            else:  # Secundaria
                grado = int(curso.nombre.split()[1][0])
                edad = 11 + grado
            
            fecha_nacimiento = date.today() - timedelta(days=365 * edad + random.randint(0, 365))
            
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=f"{username}@estudiante.colegio.edu.bo",
                password='alumno123',
                first_name=nombre,
                last_name=apellido
            )
            
            # Crear alumno
            alumno = Alumno.objects.create(
                user=user,
                curso=curso,
                fecha_nacimiento=fecha_nacimiento,
                ci=f"{random.randint(1000000, 9999999)}",
                direccion=fake.address(),
                telefono_emergencia=f"7{random.randint(1000000, 9999999)}",
                grupo_sanguineo=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
                alergias=random.choice(['Ninguna', 'Polvo', 'Maní', 'Lactosa', 'Polen']) if random.random() < 0.3 else 'Ninguna'
            )
            
            # Asignar padres (1-2 padres por alumno)
            num_padres = random.choices([1, 2], weights=[0.3, 0.7])[0]
            padres_alumno = random.sample(padres_disponibles, min(num_padres, len(padres_disponibles)))
            alumno.padres.set(padres_alumno)
            
            alumnos.append(alumno)
    
    print(f"✓ {len(alumnos)} alumnos creados exitosamente")
    return alumnos

def crear_notas_masivas(alumnos, materias):
    """Crear notas para todos los periodos y materias"""
    print(f"\n📝 Generando notas masivas...")
    notas_creadas = 0
    
    for periodo in CONFIG['periodos']:
        print(f"  📊 Creando notas para {periodo}...")
        
        for alumno in alumnos:
            # Obtener materias del curso del alumno
            materias_curso = [m for m in materias if m.curso == alumno.curso]
            
            # Generar perfil del alumno (excelente, bueno, regular, malo)
            perfil_alumno = random.choices(
                ['excelente', 'bueno', 'regular', 'malo'],
                weights=[0.15, 0.35, 0.35, 0.15]
            )[0]
            
            # Rangos de notas según el perfil
            rangos_notas = {
                'excelente': (85, 100),
                'bueno': (70, 89),
                'regular': (60, 79),
                'malo': (40, 69)
            }
            
            for materia in materias_curso:
                # 80% de probabilidad de tener nota en cada materia/periodo
                if random.random() < CONFIG['notas_por_periodo']:
                    rango = rangos_notas[perfil_alumno]
                    valor = random.randint(rango[0], rango[1])
                    
                    # Añadir variabilidad
                    valor += random.randint(-5, 5)
                    valor = max(0, min(100, valor))  # Mantener en rango 0-100
                    
                    # Generar observación ocasional
                    observaciones = ""
                    if random.random() < 0.3:  # 30% tienen observaciones
                        obs_positivas = [
                            "Excelente desempeño", "Muy participativo", "Demuestra interés",
                            "Trabajo destacado", "Mejora continua", "Responsable con tareas"
                        ]
                        obs_negativas = [
                            "Necesita mejorar atención", "Falta participación", "Requiere apoyo",
                            "Debe ser más constante", "Falta entregar tareas"
                        ]
                        
                        if valor >= 80:
                            observaciones = random.choice(obs_positivas)
                        elif valor < 60:
                            observaciones = random.choice(obs_negativas)
                    
                    nota = Nota.objects.create(
                        alumno=alumno,
                        materia=materia,
                        periodo=periodo,
                        valor=valor,
                        observaciones=observaciones,
                        fecha_registro=fake.date_between(start_date='-30d', end_date='today')
                    )
                    notas_creadas += 1
        
        print(f"    ✓ Notas de {periodo} creadas")
    
    print(f"✓ {notas_creadas} notas creadas en total")

def crear_asistencias_masivas(alumnos):
    """Crear registros de asistencia masivos"""
    print(f"\n📅 Generando asistencias masivas...")
    asistencias_creadas = 0
    
    # Generar asistencias para los últimos 90 días laborables
    fecha_inicio = date.today() - timedelta(days=CONFIG['asistencia_dias'])
    
    for alumno in alumnos:
        # Perfil de asistencia del alumno
        perfil_asistencia = random.choices(
            ['excelente', 'bueno', 'regular', 'malo'],
            weights=[0.4, 0.35, 0.2, 0.05]
        )[0]
        
        # Probabilidades de asistencia según perfil
        prob_asistencia = {
            'excelente': 0.95,
            'bueno': 0.85,
            'regular': 0.75,
            'malo': 0.60
        }
        
        fecha_actual = fecha_inicio
        while fecha_actual <= date.today():
            # Solo días laborables (lunes a viernes)
            if fecha_actual.weekday() < 5:
                presente = random.random() < prob_asistencia[perfil_asistencia]
                
                # Registrar por QR ocasionalmente
                por_qr = random.random() < 0.7 if presente else False
                
                asistencia = Asistencia.objects.create(
                    alumno=alumno,
                    fecha=fecha_actual,
                    presente=presente,
                    registrado_por_qr=por_qr,
                    hora_llegada=fake.time() if presente else None,
                    observaciones="Tardanza" if presente and random.random() < 0.1 else ""
                )
                asistencias_creadas += 1
            
            fecha_actual += timedelta(days=1)
    
    print(f"✓ {asistencias_creadas} registros de asistencia creados")

def crear_participaciones_masivas(alumnos, materias):
    """Crear participaciones masivas"""
    print(f"\n⭐ Generando participaciones masivas...")
    participaciones_creadas = 0
    
    # Últimos 60 días
    fecha_inicio = date.today() - timedelta(days=60)
    
    for alumno in alumnos:
        materias_curso = [m for m in materias if m.curso == alumno.curso]
        
        # Perfil de participación
        perfil_participacion = random.choices(
            ['muy_activo', 'activo', 'normal', 'pasivo'],
            weights=[0.2, 0.3, 0.35, 0.15]
        )[0]
        
        # Frecuencia según perfil (participaciones por semana)
        frecuencia = {
            'muy_activo': (3, 5),
            'activo': (2, 4),
            'normal': (1, 3),
            'pasivo': (0, 2)
        }
        
        # Generar participaciones por semana
        fecha_actual = fecha_inicio
        while fecha_actual <= date.today():
            if fecha_actual.weekday() < 5:  # Días laborables
                # ¿Hubo clases este día?
                if random.random() < 0.8:  # 80% de días hay clases
                    for materia in materias_curso:
                        # ¿Hubo esta materia hoy?
                        if random.random() < 0.4:  # 40% de probabilidad por materia/día
                            # ¿El alumno participó?
                            rango_freq = frecuencia[perfil_participacion]
                            prob_participar = random.randint(rango_freq[0], rango_freq[1]) / 10
                            
                            if random.random() < prob_participar:
                                # Calidad de la participación según perfil
                                if perfil_participacion == 'muy_activo':
                                    valor = random.choices([3, 4, 5], weights=[0.2, 0.3, 0.5])[0]
                                elif perfil_participacion == 'activo':
                                    valor = random.choices([2, 3, 4, 5], weights=[0.1, 0.3, 0.4, 0.2])[0]
                                elif perfil_participacion == 'normal':
                                    valor = random.choices([2, 3, 4], weights=[0.3, 0.5, 0.2])[0]
                                else:  # pasivo
                                    valor = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
                                
                                # Generar observación ocasional
                                observaciones = ""
                                if random.random() < 0.2:  # 20% tienen observación
                                    obs_opciones = [
                                        "Participación destacada", "Buena intervención", 
                                        "Pregunta interesante", "Respuesta correcta",
                                        "Ayudó a compañeros", "Participación tímida",
                                        "Buena actitud", "Participación voluntaria"
                                    ]
                                    observaciones = random.choice(obs_opciones)
                                
                                participacion = Participacion.objects.create(
                                    alumno=alumno,
                                    materia=materia,
                                    fecha=fecha_actual,
                                    valor=valor,
                                    observaciones=observaciones,
                                    tipo_participacion=random.choice([
                                        'oral', 'escrita', 'grupal', 'individual', 'proyecto'
                                    ])
                                )
                                participaciones_creadas += 1
            
            fecha_actual += timedelta(days=1)
    
    print(f"✓ {participaciones_creadas} participaciones creadas")

def crear_usuarios_especiales():
    """Crear usuarios especiales para testing"""
    print(f"\n👤 Creando usuarios especiales para testing...")
    
    # Usuarios de prueba simplificados
    usuarios_especiales = [
        ('maestro1', 'maestro123', 'Profesor', 'Ejemplo', 'maestro1@colegio.edu.bo'),
        ('alumno1', 'alumno123', 'Estudiante', 'Ejemplo', 'alumno1@estudiante.colegio.edu.bo'),
        ('padre1', 'padre123', 'Padre', 'Ejemplo', 'padre1@gmail.com'),
    ]
    
    for username, password, nombre, apellido, email in usuarios_especiales:
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido
            )
            print(f"  ✓ Usuario especial creado: {username}")
        else:
            print(f"  ✓ Usuario especial ya existe: {username}")

def mostrar_estadisticas():
    """Mostrar estadísticas finales de datos creados"""
    print(f"\n" + "="*50)
    print(f"📊 ESTADÍSTICAS FINALES DEL COLEGIO")
    print(f"="*50)
    
    # Contar entidades
    stats = {
        'Colegios': Colegio.objects.count(),
        'Maestros': Maestro.objects.count(),
        'Cursos': Curso.objects.count(),
        'Materias': Materia.objects.count(),
        'Alumnos': Alumno.objects.count(),
        'Padres': Padre.objects.count(),
        'Notas': Nota.objects.count(),
        'Asistencias': Asistencia.objects.count(),
        'Participaciones': Participacion.objects.count(),
    }
    
    for entidad, cantidad in stats.items():
        print(f"📈 {entidad:15}: {cantidad:,}")
    
    # Estadísticas por nivel
    print(f"\n📚 DISTRIBUCIÓN POR NIVELES:")
    for nivel in ['Inicial', 'Primaria', 'Secundaria']:
        cursos_nivel = Curso.objects.filter(nivel=nivel).count()
        alumnos_nivel = Alumno.objects.filter(curso__nivel=nivel).count()
        print(f"  {nivel:10}: {cursos_nivel} cursos, {alumnos_nivel} alumnos")
    
    # Promedios
    print(f"\n📊 PROMEDIOS:")
    if Nota.objects.exists():
        promedio_general = Nota.objects.aggregate(promedio=models.Avg('valor'))['promedio']
        print(f"  Promedio General de Notas: {promedio_general:.2f}")
    
    if Asistencia.objects.exists():
        asistencia_promedio = Asistencia.objects.filter(presente=True).count() / Asistencia.objects.count() * 100
        print(f"  Porcentaje de Asistencia: {asistencia_promedio:.1f}%")
    
    print(f"\n🎯 USUARIOS DE PRUEBA PRINCIPALES:")
    print(f"  👨‍💼 admin/admin123 (Administrador)")
    print(f"  👨‍🏫 maestro1/maestro123 (Maestro)")  
    print(f"  👨‍🎓 alumno1/alumno123 (Alumno)")
    print(f"  👨‍👩‍👧‍👦 padre1/padre123 (Padre)")
    
    print(f"\n🌐 ACCESO AL SISTEMA:")
    print(f"  Frontend: http://localhost:5173")
    print(f"  Backend API: http://localhost:8000/api")
    print(f"  Admin Panel: http://localhost:8000/admin")
    
    print(f"\n" + "="*50)
    print(f"🎉 DATOS MASIVOS CREADOS EXITOSAMENTE!")
    print(f"="*50)

def main():
    """Función principal para crear todos los datos masivos"""
    print("🚀 INICIANDO CREACIÓN DE DATOS MASIVOS PARA EL COLEGIO")
    print("="*60)
    
    try:
        # 1. Crear superusuario
        crear_superusuario()
        
        # 2. Crear colegio
        colegio = crear_colegio()
        
        # 3. Crear maestros
        maestros = crear_maestros()
        
        # 4. Crear cursos y materias
        cursos, materias = crear_cursos_y_materias(colegio, maestros)
        
        # 5. Crear padres
        padres = crear_padres()
        
        # 6. Crear alumnos
        alumnos = crear_alumnos(cursos, padres)
        
        # 7. Crear usuarios especiales
        crear_usuarios_especiales()
        
        # 8. Crear notas masivas
        crear_notas_masivas(alumnos, materias)
        
        # 9. Crear asistencias masivas
        crear_asistencias_masivas(alumnos)
        
        # 10. Crear participaciones masivas
        crear_participaciones_masivas(alumnos, materias)
        
        # 11. Mostrar estadísticas finales
        mostrar_estadisticas()
        
    except Exception as e:
        print(f"❌ Error durante la creación de datos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 