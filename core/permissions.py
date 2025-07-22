from rest_framework import permissions
from .models import Maestro, Alumno, Padre

class IsMaestroTutor(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es un maestro tutor
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            maestro = Maestro.objects.get(user=request.user)
            return maestro.cursos_tutor.exists()
        except Maestro.DoesNotExist:
            return False

class IsAlumno(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es un alumno
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            Alumno.objects.get(user=request.user)
            return True
        except Alumno.DoesNotExist:
            return False

class IsPadre(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es un padre
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            Padre.objects.get(user=request.user)
            return True
        except Padre.DoesNotExist:
            return False

class IsMaestro(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es un maestro
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        try:
            Maestro.objects.get(user=request.user)
            return True
        except Maestro.DoesNotExist:
            return False

class CanAccessCurso(permissions.BasePermission):
    """
    Permiso para verificar si el usuario puede acceder a un curso específico
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Si es admin, puede acceder a todo
        if request.user.is_superuser:
            return True
        
        # Si es maestro tutor del curso
        try:
            maestro = Maestro.objects.get(user=request.user)
            if obj.tutor == maestro:
                return True
        except Maestro.DoesNotExist:
            pass
        
        # Si es alumno del curso
        try:
            alumno = Alumno.objects.get(user=request.user)
            if alumno.curso == obj:
                return True
        except Alumno.DoesNotExist:
            pass
        
        # Si es padre de algún alumno del curso
        try:
            padre = Padre.objects.get(user=request.user)
            if padre.hijos.filter(curso=obj).exists():
                return True
        except Padre.DoesNotExist:
            pass
        
        return False

class CanAccessAlumno(permissions.BasePermission):
    """
    Permiso para verificar si el usuario puede acceder a la información de un alumno
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Si es admin, puede acceder a todo
        if request.user.is_superuser:
            return True
        
        # Si es el mismo alumno
        if hasattr(request.user, 'alumno') and request.user.alumno == obj:
            return True
        
        # Si es tutor del curso del alumno
        try:
            maestro = Maestro.objects.get(user=request.user)
            if obj.curso.tutor == maestro:
                return True
        except Maestro.DoesNotExist:
            pass
        
        # Si es padre del alumno
        try:
            padre = Padre.objects.get(user=request.user)
            if obj in padre.hijos.all():
                return True
        except Padre.DoesNotExist:
            pass
        
        return False

class CanAccessNota(permissions.BasePermission):
    """
    Permiso para verificar si el usuario puede acceder a una nota
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Si es admin, puede acceder a todo
        if request.user.is_superuser:
            return True
        
        # Si es el alumno de la nota
        try:
            alumno = Alumno.objects.get(user=request.user)
            if obj.alumno == alumno:
                return True
        except Alumno.DoesNotExist:
            pass
        
        # Si es tutor del curso del alumno
        try:
            maestro = Maestro.objects.get(user=request.user)
            if obj.alumno.curso.tutor == maestro:
                return True
        except Maestro.DoesNotExist:
            pass
        
        # Si es padre del alumno
        try:
            padre = Padre.objects.get(user=request.user)
            if obj.alumno in padre.hijos.all():
                return True
        except Padre.DoesNotExist:
            pass
        
        return False

class CanModifyNota(permissions.BasePermission):
    """
    Permiso para verificar si el usuario puede modificar una nota
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Si es admin, puede modificar todo
        if request.user.is_superuser:
            return True
        
        # Solo el tutor del curso puede modificar notas
        try:
            maestro = Maestro.objects.get(user=request.user)
            if obj.alumno.curso.tutor == maestro:
                return True
        except Maestro.DoesNotExist:
            pass
        
        return False

class CanAccessAsistencia(permissions.BasePermission):
    """
    Permiso para verificar si el usuario puede acceder a registros de asistencia
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Si es admin, puede acceder a todo
        if request.user.is_superuser:
            return True
        
        # Si es el alumno de la asistencia
        try:
            alumno = Alumno.objects.get(user=request.user)
            if obj.alumno == alumno:
                return True
        except Alumno.DoesNotExist:
            pass
        
        # Si es tutor del curso del alumno
        try:
            maestro = Maestro.objects.get(user=request.user)
            if obj.alumno.curso.tutor == maestro:
                return True
        except Maestro.DoesNotExist:
            pass
        
        # Si es padre del alumno
        try:
            padre = Padre.objects.get(user=request.user)
            if obj.alumno in padre.hijos.all():
                return True
        except Padre.DoesNotExist:
            pass
        
        return False

class CanAccessParticipacion(permissions.BasePermission):
    """
    Permiso para verificar si el usuario puede acceder a registros de participación
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Si es admin, puede acceder a todo
        if request.user.is_superuser:
            return True
        
        # Si es el alumno de la participación
        try:
            alumno = Alumno.objects.get(user=request.user)
            if obj.alumno == alumno:
                return True
        except Alumno.DoesNotExist:
            pass
        
        # Si es tutor del curso del alumno
        try:
            maestro = Maestro.objects.get(user=request.user)
            if obj.alumno.curso.tutor == maestro:
                return True
        except Maestro.DoesNotExist:
            pass
        
        # Si es padre del alumno
        try:
            padre = Padre.objects.get(user=request.user)
            if obj.alumno in padre.hijos.all():
                return True
        except Padre.DoesNotExist:
            pass
        
        return False 