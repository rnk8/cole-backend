#!/usr/bin/env python
"""
Script OPTIMIZADO para crear datos de prueba del Sistema de Información del Colegio
Versión optimizada con bulk_create, transacciones atómicas y limpieza de datos
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
from django.db import models, transaction
from core.models import (
    Colegio, Curso, Materia, Maestro, Alumno, Padre, 
    Nota, Asistencia, Participacion
)

fake = Faker('es_ES')  # Datos en español

# Configuración de datos masivos OPTIMIZADA
CONFIG = {
    'maestros': 30,           # Reducido para optimización
    'cursos_por_nivel': {     
        'Inicial': ['Inicial 3', 'Inicial 4', 'Inicial 5'],
        'Primaria': [f'Primaria {i}°' for i in range(1, 7)],
        'Secundaria': [f'Secundaria {i}°' for i in range(1, 7)]
    },
    'secciones': ['A', 'B'],  # Reducido a 2 secciones para optimización
    'alumnos_por_seccion': (15, 20),  # Rango optimizado
    'materias_por_nivel': {
        'Inicial': ['Desarrollo Cognitivo', 'Desarrollo Motor', 'Desarrollo Social', 'Expresión Artística', 'Música'],
        'Primaria': ['Matemáticas', 'Lenguaje', 'Ciencias Naturales', 'Estudios Sociales', 'Educación Física', 'Arte', 'Música', 'Inglés'],
        'Secundaria': ['Matemáticas', 'Física', 'Química', 'Biología', 'Historia', 'Geografía', 'Literatura', 'Filosofía', 'Inglés', 'Educación Física', 'Arte', 'Informática']
    },
    'periodos': ['2024-T1', '2024-T2', '2024-T3', '2024-T4'],
    'notas_por_periodo': 0.9,  # 90% de alumnos tienen notas
    'asistencia_dias': 60,     # Reducido a 60 días para optimización
    'participaciones_factor': 0.3,  # Factor para reducir participaciones
}

def limpiar_datos():
    """Limpiar todos los datos excepto el superadmin"""
    print("🧹 Limpiando datos existentes (excepto superadmin)...")
    
    with transaction.atomic():
        # Obtener superadmin antes de eliminar
        superadmin = None
        try:
            superadmin = User.objects.filter(is_superuser=True).first()
        except User.DoesNotExist:
            pass
        
        # Eliminar datos en orden correcto (respetando foreign keys)
        Participacion.objects.all().delete()
        Asistencia.objects.all().delete()
        Nota.objects.all().delete()
        
        # Limpiar relaciones many-to-many antes de eliminar alumnos
        for alumno in Alumno.objects.all():
            alumno.padres.clear()
        
        Alumno.objects.all().delete()
        Padre.objects.all().delete()
        Materia.objects.all().delete()
        Curso.objects.all().delete()
        Maestro.objects.all().delete()
        Colegio.objects.all().delete()
        
        # Eliminar usuarios excepto superadmin
        users_to_delete = User.objects.all()
        if superadmin:
            users_to_delete = users_to_delete.exclude(id=superadmin.id)
        users_to_delete.delete()
        
        print("✓ Datos limpiados exitosamente")

def generar_username_batch(nombres, apellidos, tipo=''):
    """Generar usernames únicos en lote"""
    usernames = []
    used_usernames = set(User.objects.values_list('username', flat=True))
    
    for nombre, apellido in zip(nombres, apellidos):
        base = f"{nombre.lower()}.{apellido.lower().split()[0]}"
        if tipo:
            base = f"{tipo}.{base}"
        
        # Remover caracteres especiales
        base = ''.join(c for c in base if c.isalnum() or c in '._')
        
        # Asegurar unicidad
        counter = 1
        username = base
        while username in used_usernames:
            username = f"{base}{counter}"
            counter += 1
        
        used_usernames.add(username)
        usernames.append(username)
    
    return usernames

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
    colegio = Colegio.objects.create(
        nombre="Unidad Educativa San José",
        direccion="Av. 6 de Agosto #2845, Zona San Pedro, La Paz",
        latitud=-16.5000,
        longitud=-68.1193,
        token_qr='QR_COLEGIO_SAN_JOSE_2024'
    )
    print(f"✓ Colegio creado: {colegio.nombre}")
    return colegio

@transaction.atomic
def crear_maestros():
    """Crear maestros usando bulk_create"""
    print(f"📚 Creando {CONFIG['maestros']} maestros...")
    
    especialidades = [
        'Matemáticas', 'Física', 'Química', 'Biología', 'Historia', 'Geografía',
        'Literatura', 'Filosofía', 'Inglés', 'Educación Física', 'Arte', 
        'Música', 'Informática', 'Psicología', 'Pedagogía', 'Educación Inicial'
    ]
    
    # Generar datos en lote
    nombres = [fake.first_name() for _ in range(CONFIG['maestros'])]
    apellidos = [fake.last_name() for _ in range(CONFIG['maestros'])]
    usernames = generar_username_batch(nombres, apellidos, 'prof')
    
    # Crear usuarios en lote
    users_to_create = []
    for i in range(CONFIG['maestros']):
        users_to_create.append(User(
            username=usernames[i],
            email=f"{usernames[i]}@colegio.edu.bo",
            first_name=nombres[i],
            last_name=apellidos[i]
        ))
    
    # Pre-hashear la contraseña una sola vez
    from django.contrib.auth.hashers import make_password
    password_hash = make_password('maestro123')
    
    # Asignar la contraseña hasheada a todos los usuarios
    for user_data in users_to_create:
        user_data.password = password_hash
    
    users = User.objects.bulk_create(users_to_create)
    
    # Crear maestros en lote
    maestros_to_create = []
    for i, user in enumerate(users):
        maestros_to_create.append(Maestro(
            user=user,
            telefono=f"7{random.randint(1000000, 9999999)}",
            especialidad=random.choice(especialidades),
            grado_academico=random.choice(['Licenciatura', 'Maestría', 'Doctorado']),
            años_experiencia=random.randint(1, 25),
            fecha_ingreso=fake.date_between(start_date='-10y', end_date='today')
        ))
    
    maestros = Maestro.objects.bulk_create(maestros_to_create)
    print(f"✓ {len(maestros)} maestros creados")
    return maestros

@transaction.atomic
def crear_cursos_y_materias(colegio, maestros):
    """Crear cursos y materias usando bulk_create"""
    print("🏫 Creando cursos y materias...")
    
    cursos_to_create = []
    maestros_list = list(maestros)
    maestro_index = 0
    
    # Crear cursos
    for nivel, cursos_nivel in CONFIG['cursos_por_nivel'].items():
        for curso_nombre in cursos_nivel:
            for seccion in CONFIG['secciones']:
                nombre_completo = f"{curso_nombre} - Sección {seccion}"
                tutor = maestros_list[maestro_index % len(maestros_list)]
                maestro_index += 1
                
                cursos_to_create.append(Curso(
                    nombre=nombre_completo,
                    nivel=nivel,
                    seccion=seccion,
                    año_academico=2024,
                    capacidad_maxima=random.randint(20, 30),
                    colegio=colegio,
                    tutor=tutor
                ))
    
    cursos = Curso.objects.bulk_create(cursos_to_create)
    
    # Crear materias
    materias_to_create = []
    for curso in cursos:
        materias_nivel = CONFIG['materias_por_nivel'][curso.nivel]
        for materia_nombre in materias_nivel:
            maestro_materia = random.choice(maestros_list)
            
            materias_to_create.append(Materia(
                nombre=materia_nombre,
                curso=curso,
                maestro=maestro_materia,
                horas_semanales=random.randint(2, 6),
                descripcion=f"Materia de {materia_nombre} para {curso.nombre}",
                codigo=f"{curso.id}-{materia_nombre[:3].upper()}"
            ))
    
    materias = Materia.objects.bulk_create(materias_to_create)
    print(f"✓ {len(cursos)} cursos y {len(materias)} materias creados")
    return cursos, materias

@transaction.atomic
def crear_padres():
    """Crear padres usando bulk_create"""
    print("👨‍👩‍👧‍👦 Creando padres de familia...")
    
    num_familias = 80  # Optimizado
    padres_to_create_users = []
    padres_to_create = []
    
    # Generar datos para padres y madres
    nombres_padres = [fake.first_name_male() for _ in range(num_familias)]
    nombres_madres = [fake.first_name_female() for _ in range(int(num_familias * 0.8))]
    apellidos_familias = [fake.last_name() for _ in range(num_familias)]
    
    # Preparar usernames
    all_nombres = nombres_padres + nombres_madres
    all_apellidos = apellidos_familias + apellidos_familias[:len(nombres_madres)]
    all_tipos = ['padre'] * len(nombres_padres) + ['madre'] * len(nombres_madres)
    
    usernames = generar_username_batch(all_nombres, all_apellidos, '')
    
    # Crear usuarios
    for i, (nombre, apellido, tipo) in enumerate(zip(all_nombres, all_apellidos, all_tipos)):
        padres_to_create_users.append(User(
            username=usernames[i],
            email=f"{usernames[i]}@gmail.com",
            first_name=nombre,
            last_name=apellido
        ))
    
    # Pre-hashear la contraseña una sola vez
    from django.contrib.auth.hashers import make_password
    password_hash = make_password('padre123')
    
    # Asignar la contraseña hasheada a todos los usuarios
    for user_data in padres_to_create_users:
        user_data.password = password_hash
    
    users = User.objects.bulk_create(padres_to_create_users)
    
    # Crear padres
    for i, user in enumerate(users):
        familia_index = i if i < num_familias else i - num_familias
        direccion_familia = fake.address()
        
        padres_to_create.append(Padre(
            user=user,
            telefono=f"7{random.randint(1000000, 9999999)}",
            ci=f"{random.randint(1000000, 9999999)}",
            ocupacion=fake.job(),
            direccion=direccion_familia
        ))
    
    padres = Padre.objects.bulk_create(padres_to_create)
    print(f"✓ {len(padres)} padres creados")
    return padres

@transaction.atomic
def crear_alumnos(cursos, padres):
    """Crear alumnos usando bulk_create"""
    print("👨‍🎓 Creando alumnos...")
    
    alumnos_to_create_users = []
    alumnos_to_create = []
    padres_list = list(padres)
    curso_alumnos_info = []  # Para guardar info de cada curso
    
    # Primera pasada: generar todos los datos y contar exactamente
    for curso in cursos:
        num_alumnos = random.randint(*CONFIG['alumnos_por_seccion'])
        
        # Generar datos del curso
        nombres = [fake.first_name() for _ in range(num_alumnos)]
        apellidos = [fake.last_name() for _ in range(num_alumnos)]
        usernames = generar_username_batch(nombres, apellidos, 'est')
        
        # Guardar info del curso para segunda pasada
        curso_info = {
            'curso': curso,
            'num_alumnos': num_alumnos,
            'nombres': nombres,
            'apellidos': apellidos,
            'usernames': usernames
        }
        curso_alumnos_info.append(curso_info)
        
        # Crear usuarios para este curso
        for i in range(num_alumnos):
            alumnos_to_create_users.append(User(
                username=usernames[i],
                email=f"{usernames[i]}@estudiante.colegio.edu.bo",
                first_name=nombres[i],
                last_name=apellidos[i]
            ))
    
    # Pre-hashear la contraseña una sola vez
    from django.contrib.auth.hashers import make_password
    password_hash = make_password('alumno123')
    
    # Asignar la contraseña hasheada a todos los usuarios
    for user_data in alumnos_to_create_users:
        user_data.password = password_hash
    
    # Crear todos los usuarios
    users = User.objects.bulk_create(alumnos_to_create_users)
    
    # Segunda pasada: crear alumnos usando los usuarios creados
    user_index = 0
    for curso_info in curso_alumnos_info:
        curso = curso_info['curso']
        num_alumnos = curso_info['num_alumnos']
        
        for i in range(num_alumnos):
            user = users[user_index]
            
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
            
            alumnos_to_create.append(Alumno(
                user=user,
                curso=curso,
                fecha_nacimiento=fecha_nacimiento,
                ci=f"{random.randint(1000000, 9999999)}",
                direccion=fake.address(),
                telefono_emergencia=f"7{random.randint(1000000, 9999999)}",
                grupo_sanguineo=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
                alergias=random.choice(['Ninguna', 'Polvo', 'Maní', 'Lactosa', 'Polen']) if random.random() < 0.3 else 'Ninguna'
            ))
            
            user_index += 1
    
    alumnos = Alumno.objects.bulk_create(alumnos_to_create)
    
    # Crear relaciones alumno-padre en lote
    for alumno in alumnos:
        num_padres = random.choices([1, 2], weights=[0.3, 0.7])[0]
        padres_alumno = random.sample(padres_list, min(num_padres, len(padres_list)))
        alumno.padres.set(padres_alumno)
    
    print(f"✓ {len(alumnos)} alumnos creados")
    return alumnos

@transaction.atomic
def crear_notas_masivas(alumnos, materias):
    """Crear notas usando bulk_create"""
    print("📝 Generando notas...")
    
    notas_to_create = []
    materias_by_curso = {}
    
    # Organizar materias por curso para optimización
    for materia in materias:
        if materia.curso_id not in materias_by_curso:
            materias_by_curso[materia.curso_id] = []
        materias_by_curso[materia.curso_id].append(materia)
    
    for periodo in CONFIG['periodos']:
        for alumno in alumnos:
            materias_curso = materias_by_curso.get(alumno.curso_id, [])
            
            # Perfil del alumno
            perfil_alumno = random.choices(
                ['excelente', 'bueno', 'regular', 'malo'],
                weights=[0.15, 0.35, 0.35, 0.15]
            )[0]
            
            rangos_notas = {
                'excelente': (85, 100),
                'bueno': (70, 89),
                'regular': (60, 79),
                'malo': (40, 69)
            }
            
            for materia in materias_curso:
                if random.random() < CONFIG['notas_por_periodo']:
                    rango = rangos_notas[perfil_alumno]
                    valor = random.randint(rango[0], rango[1])
                    valor += random.randint(-5, 5)
                    valor = max(0, min(100, valor))
                    
                    observaciones = ""
                    if random.random() < 0.2:
                        obs_opciones = [
                            "Excelente desempeño", "Muy participativo", "Demuestra interés",
                            "Trabajo destacado", "Mejora continua", "Necesita apoyo"
                        ]
                        observaciones = random.choice(obs_opciones)
                    
                    notas_to_create.append(Nota(
                        alumno=alumno,
                        materia=materia,
                        periodo=periodo,
                        valor=valor,
                        observaciones=observaciones,
                        fecha_registro=fake.date_between(start_date='-30d', end_date='today')
                    ))
    
    # Crear en lotes de 1000 para evitar problemas de memoria
    batch_size = 1000
    for i in range(0, len(notas_to_create), batch_size):
        batch = notas_to_create[i:i + batch_size]
        Nota.objects.bulk_create(batch, ignore_conflicts=True)
    
    print(f"✓ {len(notas_to_create)} notas creadas")

@transaction.atomic
def crear_asistencias_masivas(alumnos):
    """Crear asistencias usando bulk_create"""
    print("📅 Generando asistencias...")
    
    asistencias_to_create = []
    fecha_inicio = date.today() - timedelta(days=CONFIG['asistencia_dias'])
    
    for alumno in alumnos:
        perfil_asistencia = random.choices(
            ['excelente', 'bueno', 'regular', 'malo'],
            weights=[0.4, 0.35, 0.2, 0.05]
        )[0]
        
        prob_asistencia = {
            'excelente': 0.95,
            'bueno': 0.85,
            'regular': 0.75,
            'malo': 0.60
        }
        
        fecha_actual = fecha_inicio
        while fecha_actual <= date.today():
            if fecha_actual.weekday() < 5:  # Solo días laborables
                presente = random.random() < prob_asistencia[perfil_asistencia]
                por_qr = random.random() < 0.7 if presente else False
                
                asistencias_to_create.append(Asistencia(
                    alumno=alumno,
                    fecha=fecha_actual,
                    presente=presente,
                    registrado_por_qr=por_qr,
                    hora_llegada=fake.time() if presente else None,
                    observaciones="Tardanza" if presente and random.random() < 0.1 else ""
                ))
            
            fecha_actual += timedelta(days=1)
    
    # Crear en lotes
    batch_size = 1000
    for i in range(0, len(asistencias_to_create), batch_size):
        batch = asistencias_to_create[i:i + batch_size]
        Asistencia.objects.bulk_create(batch, ignore_conflicts=True)
    
    print(f"✓ {len(asistencias_to_create)} asistencias creadas")

@transaction.atomic
def crear_participaciones_masivas(alumnos, materias):
    """Crear participaciones usando bulk_create"""
    print("⭐ Generando participaciones...")
    
    participaciones_to_create = []
    materias_by_curso = {}
    
    # Organizar materias por curso
    for materia in materias:
        if materia.curso_id not in materias_by_curso:
            materias_by_curso[materia.curso_id] = []
        materias_by_curso[materia.curso_id].append(materia)
    
    fecha_inicio = date.today() - timedelta(days=30)  # Último mes solamente
    
    for alumno in alumnos:
        materias_curso = materias_by_curso.get(alumno.curso_id, [])
        
        perfil_participacion = random.choices(
            ['muy_activo', 'activo', 'normal', 'pasivo'],
            weights=[0.2, 0.3, 0.35, 0.15]
        )[0]
        
        frecuencia = {
            'muy_activo': 0.4,
            'activo': 0.3,
            'normal': 0.2,
            'pasivo': 0.1
        }
        
        # Generar participaciones de forma más eficiente
        for materia in materias_curso:
            num_participaciones = int(15 * frecuencia[perfil_participacion] * CONFIG['participaciones_factor'])
            
            for _ in range(num_participaciones):
                fecha_participacion = fake.date_between(start_date=fecha_inicio, end_date=date.today())
                
                if perfil_participacion == 'muy_activo':
                    valor = random.choices([3, 4, 5], weights=[0.2, 0.3, 0.5])[0]
                elif perfil_participacion == 'activo':
                    valor = random.choices([2, 3, 4, 5], weights=[0.1, 0.3, 0.4, 0.2])[0]
                elif perfil_participacion == 'normal':
                    valor = random.choices([2, 3, 4], weights=[0.3, 0.5, 0.2])[0]
                else:
                    valor = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
                
                participaciones_to_create.append(Participacion(
                    alumno=alumno,
                    materia=materia,
                    fecha=fecha_participacion,
                    valor=valor,
                    observaciones="",
                    tipo_participacion=random.choice(['oral', 'escrita', 'grupal', 'individual', 'proyecto'])
                ))
    
    # Crear en lotes
    batch_size = 1000
    for i in range(0, len(participaciones_to_create), batch_size):
        batch = participaciones_to_create[i:i + batch_size]
        Participacion.objects.bulk_create(batch)
    
    print(f"✓ {len(participaciones_to_create)} participaciones creadas")

def crear_usuarios_especiales():
    """Crear usuarios especiales para testing"""
    print("👤 Creando usuarios de prueba...")
    
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

def mostrar_estadisticas():
    """Mostrar estadísticas finales"""
    print(f"\n" + "="*50)
    print(f"📊 ESTADÍSTICAS FINALES DEL COLEGIO")
    print(f"="*50)
    
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
    
    print(f"\n🎯 USUARIOS DE PRUEBA:")
    print(f"  👨‍💼 admin/admin123 (Administrador)")
    print(f"  👨‍🏫 maestro1/maestro123 (Maestro)")  
    print(f"  👨‍🎓 alumno1/alumno123 (Alumno)")
    print(f"  👨‍👩‍👧‍👦 padre1/padre123 (Padre)")
    
    print(f"\n" + "="*50)
    print(f"🚀 DATOS CREADOS EXITOSAMENTE!")
    print(f"="*50)

def main():
    """Función principal optimizada"""
    start_time = datetime.now()
    print("🚀 INICIANDO CREACIÓN OPTIMIZADA DE DATOS MASIVOS")
    print("="*60)
    
    try:
        # 1. Limpiar datos existentes (excepto superadmin)
        limpiar_datos()
        
        # 2. Crear superusuario
        crear_superusuario()
        
        # 3. Crear colegio
        colegio = crear_colegio()
        
        # 4. Crear maestros
        maestros = crear_maestros()
        
        # 5. Crear cursos y materias
        cursos, materias = crear_cursos_y_materias(colegio, maestros)
        
        # 6. Crear padres
        padres = crear_padres()
        
        # 7. Crear alumnos
        alumnos = crear_alumnos(cursos, padres)
        
        # 8. Crear usuarios especiales
        crear_usuarios_especiales()
        
        # 9. Crear notas masivas
        crear_notas_masivas(alumnos, materias)
        
        # 10. Crear asistencias masivas
        crear_asistencias_masivas(alumnos)
        
        # 11. Crear participaciones masivas
        crear_participaciones_masivas(alumnos, materias)
        
        # 12. Mostrar estadísticas finales
        mostrar_estadisticas()
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\n⏱️  Tiempo total: {duration.total_seconds():.2f} segundos")
        
    except Exception as e:
        print(f"❌ Error durante la creación de datos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 