from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.utils import timezone
from django.views.generic import TemplateView
from datetime import datetime, date, time
import math
import pickle
import os

from .models import (
    Colegio, Curso, Materia, Maestro, Alumno, Padre, 
    Nota, Asistencia, Participacion
)
from .serializers import (
    UserSerializer, ColegioSerializer, CursoSerializer, MateriaSerializer,
    MaestroSerializer, MaestroListSerializer, AlumnoSerializer, AlumnoListSerializer,
    PadreSerializer, NotaSerializer, AsistenciaSerializer, ParticipacionSerializer,
    QRAsistenciaSerializer, PrediccionSerializer
)
from .permissions import (
    IsMaestroTutor, IsAlumno, IsPadre, IsMaestro,
    CanAccessCurso, CanAccessAlumno, CanAccessNota, CanModifyNota,
    CanAccessAsistencia, CanAccessParticipacion
)

# Vistas de autenticación
class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener tokens JWT"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Agregar información del usuario al response
            user = User.objects.get(username=request.data['username'])
            user_data = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            }
            
            # Determinar el rol del usuario
            try:
                maestro = Maestro.objects.get(user=user)
                user_data['role'] = 'maestro'
                user_data['role_id'] = maestro.id
                if maestro.cursos_tutor.exists():
                    user_data['is_tutor'] = True
                    user_data['curso_tutor'] = maestro.cursos_tutor.first().id
            except Maestro.DoesNotExist:
                try:
                    alumno = Alumno.objects.get(user=user)
                    user_data['role'] = 'alumno'
                    user_data['role_id'] = alumno.id
                    user_data['curso'] = alumno.curso.id
                except Alumno.DoesNotExist:
                    try:
                        padre = Padre.objects.get(user=user)
                        user_data['role'] = 'padre'
                        user_data['role_id'] = padre.id
                        user_data['hijos'] = list(padre.hijos.values_list('id', flat=True))
                    except Padre.DoesNotExist:
                        user_data['role'] = 'admin' if user.is_superuser else 'unknown'
            
            response.data['user'] = user_data
        return response

# Vistas para Colegios
class ColegioListCreateView(generics.ListCreateAPIView):
    queryset = Colegio.objects.all()
    serializer_class = ColegioSerializer
    permission_classes = [permissions.IsAuthenticated]

class ColegioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Colegio.objects.all()
    serializer_class = ColegioSerializer
    permission_classes = [permissions.IsAdminUser]

# Vistas para Maestros
class MaestroListCreateView(generics.ListCreateAPIView):
    queryset = Maestro.objects.all()
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return MaestroListSerializer
        return MaestroSerializer

class MaestroDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Maestro.objects.all()
    serializer_class = MaestroSerializer
    permission_classes = [permissions.IsAdminUser]

# Vistas para Cursos
class CursoListCreateView(generics.ListCreateAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Curso.objects.all()
        
        # Si es maestro, solo ve sus cursos como tutor
        try:
            maestro = Maestro.objects.get(user=user)
            return maestro.cursos_tutor.all()
        except Maestro.DoesNotExist:
            pass
        
        # Si es alumno, solo ve su curso
        try:
            alumno = Alumno.objects.get(user=user)
            return Curso.objects.filter(id=alumno.curso.id)
        except Alumno.DoesNotExist:
            pass
        
        # Si es padre, ve los cursos de sus hijos
        try:
            padre = Padre.objects.get(user=user)
            return Curso.objects.filter(alumnos__in=padre.hijos.all()).distinct()
        except Padre.DoesNotExist:
            pass
        
        return Curso.objects.none()

class CursoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessCurso]

# Vistas para Materias
class MateriaListCreateView(generics.ListCreateAPIView):
    serializer_class = MateriaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        curso_id = self.request.query_params.get('curso', None)
        if curso_id:
            return Materia.objects.filter(curso_id=curso_id)
        return Materia.objects.all()

class MateriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [permissions.IsAdminUser]

# Vistas para Padres
class PadreListCreateView(generics.ListCreateAPIView):
    queryset = Padre.objects.all()
    serializer_class = PadreSerializer
    permission_classes = [permissions.IsAdminUser]

class PadreDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Padre.objects.all()
    serializer_class = PadreSerializer
    permission_classes = [permissions.IsAdminUser]

# Vistas para Alumnos
class AlumnoListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AlumnoListSerializer
        return AlumnoSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Alumno.objects.all()
        
        # Si es maestro tutor, solo ve alumnos de su curso
        try:
            maestro = Maestro.objects.get(user=user)
            return Alumno.objects.filter(curso__tutor=maestro)
        except Maestro.DoesNotExist:
            pass
        
        # Si es alumno, solo se ve a sí mismo
        try:
            alumno = Alumno.objects.get(user=user)
            return Alumno.objects.filter(id=alumno.id)
        except Alumno.DoesNotExist:
            pass
        
        # Si es padre, ve a sus hijos
        try:
            padre = Padre.objects.get(user=user)
            return padre.hijos.all()
        except Padre.DoesNotExist:
            pass
        
        return Alumno.objects.none()

class AlumnoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessAlumno]

# Vistas para Notas
class NotaListCreateView(generics.ListCreateAPIView):
    serializer_class = NotaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Nota.objects.all()
        
        # Filtros por parámetros de query
        alumno_id = self.request.query_params.get('alumno', None)
        materia_id = self.request.query_params.get('materia', None)
        periodo = self.request.query_params.get('periodo', None)
        
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        if materia_id:
            queryset = queryset.filter(materia_id=materia_id)
        if periodo:
            queryset = queryset.filter(periodo=periodo)
        
        # Filtros por rol
        if user.is_superuser:
            return queryset
        
        # Si es maestro tutor, solo ve notas de su curso
        try:
            maestro = Maestro.objects.get(user=user)
            return queryset.filter(alumno__curso__tutor=maestro)
        except Maestro.DoesNotExist:
            pass
        
        # Si es alumno, solo ve sus notas
        try:
            alumno = Alumno.objects.get(user=user)
            return queryset.filter(alumno=alumno)
        except Alumno.DoesNotExist:
            pass
        
        # Si es padre, ve notas de sus hijos
        try:
            padre = Padre.objects.get(user=user)
            return queryset.filter(alumno__in=padre.hijos.all())
        except Padre.DoesNotExist:
            pass
        
        return Nota.objects.none()
    
    def perform_create(self, serializer):
        # Solo maestros tutores pueden crear notas
        try:
            maestro = Maestro.objects.get(user=self.request.user)
            # Verificar que la materia pertenezca al curso del tutor
            materia = serializer.validated_data['materia']
            if materia.curso.tutor != maestro:
                raise permissions.PermissionDenied("No puedes registrar notas para este curso")
        except Maestro.DoesNotExist:
            if not self.request.user.is_superuser:
                raise permissions.PermissionDenied("Solo los maestros tutores pueden registrar notas")
        
        serializer.save()

class NotaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Nota.objects.all()
    serializer_class = NotaSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessNota]
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), CanModifyNota()]
        return [permissions.IsAuthenticated(), CanAccessNota()]

# Vistas para Asistencia
class AsistenciaListCreateView(generics.ListCreateAPIView):
    serializer_class = AsistenciaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Asistencia.objects.all()
        
        # Filtros por parámetros de query
        alumno_id = self.request.query_params.get('alumno', None)
        fecha = self.request.query_params.get('fecha', None)
        
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        if fecha:
            queryset = queryset.filter(fecha=fecha)
        
        # Filtros por rol
        if user.is_superuser:
            return queryset
        
        # Si es maestro tutor, solo ve asistencia de su curso
        try:
            maestro = Maestro.objects.get(user=user)
            return queryset.filter(alumno__curso__tutor=maestro)
        except Maestro.DoesNotExist:
            pass
        
        # Si es alumno, solo ve su asistencia
        try:
            alumno = Alumno.objects.get(user=user)
            return queryset.filter(alumno=alumno)
        except Alumno.DoesNotExist:
            pass
        
        # Si es padre, ve asistencia de sus hijos
        try:
            padre = Padre.objects.get(user=user)
            return queryset.filter(alumno__in=padre.hijos.all())
        except Padre.DoesNotExist:
            pass
        
        return Asistencia.objects.none()

class AsistenciaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessAsistencia]

# Vista especial para registro de asistencia por QR
class QRAsistenciaView(APIView):
    permission_classes = [IsAlumno]
    
    def post(self, request):
        serializer = QRAsistenciaSerializer(data=request.data)
        if serializer.is_valid():
            qr_token = serializer.validated_data['qr_token']
            latitud = serializer.validated_data['latitud']
            longitud = serializer.validated_data['longitud']
            
            try:
                alumno = Alumno.objects.get(user=request.user)
                colegio = alumno.curso.colegio
                
                # Verificar token QR
                if str(colegio.token_qr) != qr_token:
                    return Response(
                        {'error': 'Token QR inválido'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Verificar ubicación (tolerancia en grados)
                tolerance = getattr(settings, 'QR_LOCATION_TOLERANCE', 0.001)
                lat_diff = abs(colegio.latitud - latitud)
                lng_diff = abs(colegio.longitud - longitud)
                
                if lat_diff > tolerance or lng_diff > tolerance:
                    return Response(
                        {'error': 'Ubicación fuera del rango permitido'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Verificar horario
                now = timezone.now()
                start_time = datetime.strptime(
                    getattr(settings, 'QR_ATTENDANCE_TIME_START', '07:00'), 
                    '%H:%M'
                ).time()
                end_time = datetime.strptime(
                    getattr(settings, 'QR_ATTENDANCE_TIME_END', '08:30'), 
                    '%H:%M'
                ).time()
                
                current_time = now.time()
                if not (start_time <= current_time <= end_time):
                    return Response(
                        {'error': 'Fuera del horario permitido para registro de asistencia'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Registrar asistencia
                asistencia, created = Asistencia.objects.get_or_create(
                    alumno=alumno,
                    fecha=now.date(),
                    defaults={
                        'presente': True,
                        'registrado_por_qr': True
                    }
                )
                
                if not created and asistencia.presente:
                    return Response(
                        {'message': 'Asistencia ya registrada para hoy'}, 
                        status=status.HTTP_200_OK
                    )
                elif not created:
                    asistencia.presente = True
                    asistencia.registrado_por_qr = True
                    asistencia.save()
                
                return Response(
                    {'message': 'Asistencia registrada exitosamente'}, 
                    status=status.HTTP_201_CREATED
                )
                
            except Alumno.DoesNotExist:
                return Response(
                    {'error': 'Usuario no es un alumno'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Vistas para Participaciones
class ParticipacionListCreateView(generics.ListCreateAPIView):
    serializer_class = ParticipacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Participacion.objects.all()
        
        # Filtros por parámetros de query
        alumno_id = self.request.query_params.get('alumno', None)
        materia_id = self.request.query_params.get('materia', None)
        fecha = self.request.query_params.get('fecha', None)
        
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        if materia_id:
            queryset = queryset.filter(materia_id=materia_id)
        if fecha:
            queryset = queryset.filter(fecha=fecha)
        
        # Filtros por rol
        if user.is_superuser:
            return queryset
        
        # Si es maestro tutor, solo ve participaciones de su curso
        try:
            maestro = Maestro.objects.get(user=user)
            return queryset.filter(alumno__curso__tutor=maestro)
        except Maestro.DoesNotExist:
            pass
        
        # Si es alumno, solo ve sus participaciones
        try:
            alumno = Alumno.objects.get(user=user)
            return queryset.filter(alumno=alumno)
        except Alumno.DoesNotExist:
            pass
        
        # Si es padre, ve participaciones de sus hijos
        try:
            padre = Padre.objects.get(user=user)
            return queryset.filter(alumno__in=padre.hijos.all())
        except Padre.DoesNotExist:
            pass
        
        return Participacion.objects.none()
    
    def perform_create(self, serializer):
        # Solo maestros tutores pueden crear participaciones
        try:
            maestro = Maestro.objects.get(user=self.request.user)
            # Verificar que la materia pertenezca al curso del tutor
            materia = serializer.validated_data['materia']
            if materia.curso.tutor != maestro:
                raise permissions.PermissionDenied("No puedes registrar participaciones para este curso")
        except Maestro.DoesNotExist:
            if not self.request.user.is_superuser:
                raise permissions.PermissionDenied("Solo los maestros tutores pueden registrar participaciones")
        
        serializer.save()

class ParticipacionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Participacion.objects.all()
    serializer_class = ParticipacionSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessParticipacion]

# Vista para predicción de rendimiento
class PrediccionRendimientoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, alumno_id, periodo):
        try:
            alumno = get_object_or_404(Alumno, id=alumno_id)
            
            # Verificar permisos
            if not request.user.is_superuser:
                try:
                    if request.user.alumno != alumno:
                        # Verificar si es tutor del curso
                        maestro = Maestro.objects.get(user=request.user)
                        if alumno.curso.tutor != maestro:
                            # Verificar si es padre del alumno
                            padre = Padre.objects.get(user=request.user)
                            if alumno not in padre.hijos.all():
                                return Response(
                                    {'error': 'No tienes permisos para ver esta predicción'}, 
                                    status=status.HTTP_403_FORBIDDEN
                                )
                except (Alumno.DoesNotExist, Maestro.DoesNotExist, Padre.DoesNotExist):
                    return Response(
                        {'error': 'No tienes permisos para ver esta predicción'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Calcular variables para la predicción
            prediccion_data = self._calcular_prediccion(alumno, periodo)
            
            serializer = PrediccionSerializer(prediccion_data)
            return Response(serializer.data)
            
        except Alumno.DoesNotExist:
            return Response(
                {'error': 'Alumno no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _calcular_prediccion(self, alumno, periodo_actual):
        """Calcular predicción de rendimiento usando datos históricos"""
        # Obtener promedio de notas anteriores
        notas_anteriores = Nota.objects.filter(
            alumno=alumno,
            periodo__lt=periodo_actual  # Periodos anteriores
        ).values_list('valor', flat=True)
        
        promedio_notas = sum(notas_anteriores) / len(notas_anteriores) if notas_anteriores else 0
        
        # Calcular porcentaje de asistencia del periodo actual
        asistencias = Asistencia.objects.filter(alumno=alumno, fecha__year=2024)  # Año actual
        total_dias = asistencias.count()
        dias_presente = asistencias.filter(presente=True).count()
        porcentaje_asistencia = (dias_presente / total_dias * 100) if total_dias > 0 else 100
        
        # Calcular promedio de participaciones
        participaciones = Participacion.objects.filter(alumno=alumno).values_list('valor', flat=True)
        promedio_participaciones = sum(participaciones) / len(participaciones) if participaciones else 0
        
        # Predicción simple basada en pesos
        # Esta es una implementación simplificada. En producción usarías un modelo ML entrenado
        peso_notas = 0.5
        peso_asistencia = 0.3
        peso_participaciones = 0.2
        
        prediccion_numerica = (
            promedio_notas * peso_notas +
            (porcentaje_asistencia / 100 * 100) * peso_asistencia +
            (promedio_participaciones / 5 * 100) * peso_participaciones
        )
        
        # Clasificación basada en la predicción numérica
        if prediccion_numerica >= 85:
            clasificacion = "alto"
        elif prediccion_numerica >= 70:
            clasificacion = "medio"
        else:
            clasificacion = "bajo"
        
        return {
            'prediccion_numerica': round(prediccion_numerica, 2),
            'clasificacion': clasificacion,
            'promedio_notas_anteriores': round(promedio_notas, 2),
            'porcentaje_asistencia': round(porcentaje_asistencia, 2),
            'promedio_participaciones': round(promedio_participaciones, 2)
        }

# Vista para la página principal
class HomePageView(TemplateView):
    """Vista para la página principal del sistema"""
    template_name = 'core/index.html'

# Vista para información de la API
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request):
    """Vista que proporciona información básica de la API"""
    return Response({
        'message': 'API del Sistema de Información del Colegio',
        'version': '1.0',
        'documentation': 'Documentación disponible en los endpoints individuales',
        'endpoints': {
            'auth': {
                'login': '/api/auth/login/',
                'refresh': '/api/auth/refresh/',
            },
            'management': {
                'colegios': '/api/colegios/',
                'maestros': '/api/maestros/',
                'cursos': '/api/cursos/',
                'materias': '/api/materias/',
                'alumnos': '/api/alumnos/',
                'padres': '/api/padres/',
            },
            'academic': {
                'notas': '/api/notas/',
                'asistencia': '/api/asistencia/',
                'asistencia_qr': '/api/asistencia/qr/',
                'participaciones': '/api/participaciones/',
            },
            'ai': {
                'prediccion': '/api/prediccion/{alumno_id}/{periodo}/',
            }
        },
        'test_users': {
            'admin': {'username': 'admin', 'password': 'admin123'},
            'maestro': {'username': 'maestro1', 'password': 'maestro123'},
            'alumno': {'username': 'alumno1', 'password': 'alumno123'},
            'padre': {'username': 'padre1', 'password': 'padre123'},
        }
    })
