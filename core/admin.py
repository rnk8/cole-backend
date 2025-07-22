from django.contrib import admin
from .models import Colegio, Curso, Materia, Maestro, Alumno, Padre, Nota, Asistencia, Participacion

@admin.register(Colegio)
class ColegioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'latitud', 'longitud')
    search_fields = ('nombre',)

@admin.register(Maestro)
class MaestroAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'get_username', 'telefono')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def get_nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_nombre_completo.short_description = 'Nombre Completo'
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'colegio', 'tutor', 'get_num_alumnos')
    list_filter = ('colegio', 'tutor')
    search_fields = ('nombre', 'colegio__nombre')
    
    def get_num_alumnos(self, obj):
        return obj.alumnos.count()
    get_num_alumnos.short_description = 'Número de Alumnos'

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'curso', 'get_colegio')
    list_filter = ('curso__colegio', 'curso')
    search_fields = ('nombre', 'curso__nombre')
    
    def get_colegio(self, obj):
        return obj.curso.colegio.nombre
    get_colegio.short_description = 'Colegio'

@admin.register(Padre)
class PadreAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'get_username', 'telefono', 'get_num_hijos')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def get_nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_nombre_completo.short_description = 'Nombre Completo'
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_num_hijos(self, obj):
        return obj.hijos.count()
    get_num_hijos.short_description = 'Número de Hijos'

@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'get_username', 'curso', 'fecha_nacimiento')
    list_filter = ('curso', 'curso__colegio')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'curso__nombre')
    filter_horizontal = ('padres',)
    
    def get_nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_nombre_completo.short_description = 'Nombre Completo'
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('get_alumno', 'materia', 'periodo', 'valor', 'fecha_registro')
    list_filter = ('materia', 'periodo', 'materia__curso')
    search_fields = ('alumno__user__username', 'alumno__user__first_name', 'alumno__user__last_name', 'materia__nombre')
    
    def get_alumno(self, obj):
        return f"{obj.alumno.user.first_name} {obj.alumno.user.last_name}"
    get_alumno.short_description = 'Alumno'

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('get_alumno', 'fecha', 'presente', 'registrado_por_qr')
    list_filter = ('presente', 'registrado_por_qr', 'fecha', 'alumno__curso')
    search_fields = ('alumno__user__username', 'alumno__user__first_name', 'alumno__user__last_name')
    date_hierarchy = 'fecha'
    
    def get_alumno(self, obj):
        return f"{obj.alumno.user.first_name} {obj.alumno.user.last_name}"
    get_alumno.short_description = 'Alumno'

@admin.register(Participacion)
class ParticipacionAdmin(admin.ModelAdmin):
    list_display = ('get_alumno', 'materia', 'fecha', 'valor')
    list_filter = ('materia', 'fecha', 'materia__curso')
    search_fields = ('alumno__user__username', 'alumno__user__first_name', 'alumno__user__last_name', 'materia__nombre')
    date_hierarchy = 'fecha'
    
    def get_alumno(self, obj):
        return f"{obj.alumno.user.first_name} {obj.alumno.user.last_name}"
    get_alumno.short_description = 'Alumno'
