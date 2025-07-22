from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date

class Colegio(models.Model):
    """Modelo para representar un colegio"""
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    latitud = models.FloatField()
    longitud = models.FloatField()
    token_qr = models.CharField(max_length=100, unique=True)  # Token para el QR
    
    class Meta:
        verbose_name = "Colegio"
        verbose_name_plural = "Colegios"
    
    def __str__(self):
        return self.nombre

class Maestro(models.Model):
    """Modelo para representar un maestro"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    especialidad = models.CharField(max_length=100, blank=True)
    grado_academico = models.CharField(max_length=50, blank=True, choices=[
        ('Bachiller', 'Bachiller'),
        ('Licenciatura', 'Licenciatura'),
        ('Maestría', 'Maestría'),
        ('Doctorado', 'Doctorado'),
    ])
    años_experiencia = models.PositiveIntegerField(default=0)
    fecha_ingreso = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Maestro"
        verbose_name_plural = "Maestros"
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Curso(models.Model):
    """Modelo para representar un curso (sección)"""
    nombre = models.CharField(max_length=100)  # Ej: "1ro A", "2do B"
    nivel = models.CharField(max_length=50, choices=[
        ('Inicial', 'Inicial'),
        ('Primaria', 'Primaria'),
        ('Secundaria', 'Secundaria'),
    ])
    seccion = models.CharField(max_length=10)  # A, B, C, etc.
    año_academico = models.PositiveIntegerField(default=2024)
    capacidad_maxima = models.PositiveIntegerField(default=30)
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name='cursos')
    tutor = models.ForeignKey(Maestro, on_delete=models.SET_NULL, null=True, blank=True, related_name='cursos_tutor')
    
    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        unique_together = ['nombre', 'colegio']
    
    def __str__(self):
        return f"{self.nombre} - {self.colegio.nombre}"

class Materia(models.Model):
    """Modelo para representar una materia"""
    nombre = models.CharField(max_length=100)  # Ej: "Matemáticas", "Lenguaje"
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='materias')
    maestro = models.ForeignKey(Maestro, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    horas_semanales = models.PositiveIntegerField(default=2)
    codigo = models.CharField(max_length=20, blank=True)
    
    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        unique_together = ['nombre', 'curso']
    
    def __str__(self):
        return f"{self.nombre} - {self.curso.nombre}"

class Padre(models.Model):
    """Modelo para representar un padre de familia"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ci = models.CharField(max_length=20, blank=True, verbose_name="Cédula de Identidad")
    ocupacion = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Padre"
        verbose_name_plural = "Padres"
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Alumno(models.Model):
    """Modelo para representar un alumno"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='alumnos')
    padres = models.ManyToManyField(Padre, related_name='hijos', blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    ci = models.CharField(max_length=20, blank=True, verbose_name="Cédula de Identidad")
    direccion = models.CharField(max_length=255, blank=True)
    telefono_emergencia = models.CharField(max_length=20, blank=True)
    grupo_sanguineo = models.CharField(max_length=10, blank=True, choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ])
    alergias = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def nombre_completo(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def username(self):
        return self.user.username
    
    @property
    def curso_nombre(self):
        return self.curso.nombre

class Nota(models.Model):
    """Modelo para representar una nota"""
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='notas')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='notas')
    periodo = models.CharField(max_length=50)  # Ej: "2023-T1" (trimestre 1)
    valor = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    observaciones = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        unique_together = ['alumno', 'materia', 'periodo']
    
    def __str__(self):
        return f"{self.alumno.user.first_name} - {self.materia.nombre} - {self.valor}"
    
    @property
    def materia_nombre(self):
        return self.materia.nombre

class Asistencia(models.Model):
    """Modelo para representar la asistencia"""
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    presente = models.BooleanField(default=False)
    registrado_por_qr = models.BooleanField(default=False)
    hora_llegada = models.TimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ['alumno', 'fecha']
    
    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return f"{self.alumno.user.first_name} - {self.fecha} - {estado}"

class Participacion(models.Model):
    """Modelo para representar una participación"""
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='participaciones')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='participaciones')
    fecha = models.DateField()
    valor = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )  # Escala de 0 a 5
    observaciones = models.TextField(blank=True)
    tipo_participacion = models.CharField(max_length=50, choices=[
        ('oral', 'Participación Oral'),
        ('escrita', 'Participación Escrita'),
        ('grupal', 'Trabajo Grupal'),
        ('individual', 'Trabajo Individual'),
        ('proyecto', 'Proyecto'),
    ], default='oral')
    
    class Meta:
        verbose_name = "Participación"
        verbose_name_plural = "Participaciones"
    
    def __str__(self):
        return f"{self.alumno.user.first_name} - {self.materia.nombre} - {self.valor}"
