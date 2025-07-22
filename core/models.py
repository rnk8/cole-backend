from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Colegio(models.Model):
    """Modelo para representar un colegio"""
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    latitud = models.FloatField()
    longitud = models.FloatField()
    token_qr = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    
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
    
    class Meta:
        verbose_name = "Maestro"
        verbose_name_plural = "Maestros"
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Curso(models.Model):
    """Modelo para representar un curso (sección)"""
    nombre = models.CharField(max_length=100)  # Ej: "1ro A", "2do B"
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
    descripcion = models.TextField(blank=True)
    
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
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.curso.nombre}"

class Nota(models.Model):
    """Modelo para representar las notas de los alumnos"""
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='notas')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='notas')
    periodo = models.CharField(max_length=50)  # Ej: "2024-T1" (trimestre 1)
    valor = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        unique_together = ['alumno', 'materia', 'periodo']
    
    def __str__(self):
        return f"{self.alumno.user.username} - {self.materia.nombre} - {self.periodo}: {self.valor}"

class Asistencia(models.Model):
    """Modelo para representar la asistencia de los alumnos"""
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    presente = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por_qr = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ['alumno', 'fecha']
    
    def __str__(self):
        estado = "Presente" if self.presente else "Ausente"
        return f"{self.alumno.user.username} - {self.fecha} - {estado}"

class Participacion(models.Model):
    """Modelo para representar las participaciones de los alumnos"""
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='participaciones')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='participaciones')
    fecha = models.DateField()
    valor = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )  # Escala de 0 a 5
    observaciones = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Participación"
        verbose_name_plural = "Participaciones"
    
    def __str__(self):
        return f"{self.alumno.user.username} - {self.materia.nombre} - {self.fecha}: {self.valor}"
