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
    QRAsistenciaSerializer, PrediccionSerializer, HijoDashboardSerializer, 
    DetalleHijoSerializer, MaestroDashboardSerializer
)
from .permissions import (
    IsMaestroTutor, IsAlumno, IsPadre, IsMaestro,
    CanAccessCurso, CanAccessAlumno, CanAccessNota, CanModifyNota,
    CanAccessAsistencia, CanAccessParticipacion, IsPadre
)
from django.db.models import Avg, Count, Q, Case, When, FloatField, Prefetch
from django.db.models.functions import Cast
from datetime import timedelta

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

class MaestroDashboardView(APIView):
    """
    Endpoint principal para el dashboard del maestro tutor.
    Devuelve toda la información necesaria para gestionar su curso.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            maestro = Maestro.objects.get(user=request.user)
            curso_tutor = maestro.cursos_tutor.first()

            if not curso_tutor:
                return Response(
                    {'error': 'No eres tutor de ningún curso.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Obtener materias del curso
            materias = Materia.objects.filter(curso=curso_tutor)

            # Obtener período de la query, o usar el más reciente
            periodos_disponibles = list(Nota.objects.filter(alumno__curso=curso_tutor).values_list('periodo', flat=True).distinct().order_by('-periodo'))
            periodo_seleccionado = request.query_params.get('periodo', periodos_disponibles[0] if periodos_disponibles else None)
            
            # Obtener alumnos con sus notas y participaciones
            if periodo_seleccionado:
                alumnos = Alumno.objects.filter(curso=curso_tutor).prefetch_related(
                    Prefetch(
                        'notas',
                        queryset=Nota.objects.filter(periodo=periodo_seleccionado),
                        to_attr='notas_periodo'
                    ),
                    'participaciones'
                ).select_related('user')
                
                # Para el serializer, necesitamos pasar las notas filtradas
                for alumno in alumnos:
                    alumno.notas_filtradas = alumno.notas_periodo
            else:
                # Si no hay período seleccionado, obtener alumnos sin notas filtradas
                alumnos = Alumno.objects.filter(curso=curso_tutor).prefetch_related(
                    'notas', 'participaciones'
                ).select_related('user')

            data = {
                'curso': curso_tutor,
                'materias': materias,
                'alumnos': alumnos,
                'periodos': periodos_disponibles
            }
            
            serializer = MaestroDashboardSerializer(data)
            return Response(serializer.data)

        except Maestro.DoesNotExist:
            return Response({'error': 'Perfil de maestro no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en MaestroDashboardView: {str(e)}")
            return Response({'error': 'Error interno del servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

# Vistas para el Dashboard del Padre

class PadreDashboardView(APIView):
    """
    Vista mejorada para el dashboard del padre. Muestra una lista de sus hijos con información completa.
    """
    permission_classes = [permissions.IsAuthenticated, IsPadre]

    def get(self, request):
        try:
            padre = Padre.objects.get(user=request.user)
            
            # Determinar los dos períodos más recientes con notas
            periodos_recientes = list(Nota.objects.filter(
                alumno__in=padre.hijos.all()
            ).order_by('-periodo').values_list('periodo', flat=True).distinct()[:2])
            
            periodo_actual = periodos_recientes[0] if periodos_recientes else None
            periodo_anterior = periodos_recientes[1] if len(periodos_recientes) > 1 else None

            # Calcular datos de los últimos 30 días
            hace_30_dias = timezone.now().date() - timedelta(days=30)
            
            hijos = padre.hijos.all().select_related('user', 'curso').annotate(
                # Promedio de notas del período actual
                promedio_periodo=Avg(
                    'notas__valor', 
                    filter=Q(notas__periodo=periodo_actual)
                ),
                # Promedio de notas del período anterior (para comparar tendencia)
                promedio_anterior=Avg(
                    'notas__valor', 
                    filter=Q(notas__periodo=periodo_anterior)
                ) if periodo_anterior else None,
                
                # Estadísticas de asistencia (últimos 30 días)
                total_dias_clase=Count(
                    'asistencias',
                    filter=Q(asistencias__fecha__gte=hace_30_dias)
                ),
                dias_presente=Count(
                    'asistencias',
                    filter=Q(asistencias__fecha__gte=hace_30_dias, asistencias__presente=True)
                ),
                dias_ausente_mes=Count(
                    'asistencias',
                    filter=Q(asistencias__fecha__gte=hace_30_dias, asistencias__presente=False)
                ),
                
                # Estadísticas de participación (último mes)
                total_participaciones_mes=Count(
                    'participaciones',
                    filter=Q(participaciones__fecha__gte=hace_30_dias)
                ),
                promedio_participaciones=Avg(
                    'participaciones__valor',
                    filter=Q(participaciones__fecha__gte=hace_30_dias)
                )
            ).annotate(
                # Calcular porcentaje de asistencia
                porcentaje_asistencia=Case(
                    When(total_dias_clase__gt=0, then=(Cast('dias_presente', FloatField()) * 100.0 / Cast('total_dias_clase', FloatField()))),
                    default=100.0,  # Si no hay datos, asumir 100%
                    output_field=FloatField()
                )
            )

            serializer = HijoDashboardSerializer(hijos, many=True)
            
            # Agregar información adicional del dashboard
            dashboard_data = {
                'hijos': serializer.data,
                'resumen_general': self._generar_resumen_general(hijos),
                'periodo_actual': periodo_actual,
                'alertas_importantes': self._generar_alertas_importantes(hijos)
            }
            
            return Response(dashboard_data)
            
        except Padre.DoesNotExist:
            return Response(
                {'error': 'No se encontró un perfil de padre para este usuario.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _generar_resumen_general(self, hijos):
        """Generar resumen general del dashboard"""
        total_hijos = len(hijos)
        if total_hijos == 0:
            return {}
        
        # Calcular estadísticas generales
        promedios_validos = [h.promedio_periodo for h in hijos if h.promedio_periodo is not None]
        asistencias_validas = [h.porcentaje_asistencia for h in hijos if h.porcentaje_asistencia is not None]
        
        return {
            'total_hijos': total_hijos,
            'promedio_familiar': round(sum(promedios_validos) / len(promedios_validos), 1) if promedios_validos else None,
            'asistencia_promedio': round(sum(asistencias_validas) / len(asistencias_validas), 1) if asistencias_validas else None,
            'hijos_rendimiento_alto': len([p for p in promedios_validos if p >= 85]),
            'hijos_necesitan_atencion': len([p for p in promedios_validos if p < 70])
        }
    
    def _generar_alertas_importantes(self, hijos):
        """Generar alertas importantes para el dashboard principal"""
        alertas = []
        
        for hijo in hijos:
            # Alertas críticas de asistencia
            if hasattr(hijo, 'porcentaje_asistencia') and hijo.porcentaje_asistencia < 75:
                alertas.append({
                    'tipo': 'asistencia_critica',
                    'hijo_id': hijo.id,
                    'hijo_nombre': hijo.user.get_full_name(),
                    'mensaje': f'Asistencia muy baja: {hijo.porcentaje_asistencia:.0f}%',
                    'nivel': 'danger'
                })
            
            # Alertas académicas críticas
            if hasattr(hijo, 'promedio_periodo') and hijo.promedio_periodo and hijo.promedio_periodo < 60:
                alertas.append({
                    'tipo': 'academico_critico',
                    'hijo_id': hijo.id,
                    'hijo_nombre': hijo.user.get_full_name(),
                    'mensaje': f'Promedio muy bajo: {hijo.promedio_periodo:.1f}',
                    'nivel': 'danger'
                })
        
        return alertas[:5]  # Máximo 5 alertas importantes

class DetalleHijoView(APIView):
    """
    Vista mejorada para ver el detalle académico completo de un hijo específico.
    """
    permission_classes = [permissions.IsAuthenticated, IsPadre]

    def get(self, request, alumno_id):
        try:
            padre = Padre.objects.get(user=request.user)
            hijo = get_object_or_404(padre.hijos.all(), id=alumno_id)

            # Obtener todos los períodos disponibles
            periodos_disponibles = list(Nota.objects.filter(alumno=hijo).values_list('periodo', flat=True).distinct().order_by('-periodo'))
            periodo_seleccionado = request.query_params.get('periodo', periodos_disponibles[0] if periodos_disponibles else None)

            # Filtrar asistencias (últimos 60 días para mejor contexto)
            fecha_limite = timezone.now().date() - timedelta(days=60)
            asistencias = Asistencia.objects.filter(
                alumno=hijo, 
                fecha__gte=fecha_limite
            ).order_by('-fecha')

            # Pre-cargar materias con sus notas y participaciones
            materias = Materia.objects.filter(curso=hijo.curso).prefetch_related(
                Prefetch(
                    'notas',
                    queryset=Nota.objects.filter(alumno=hijo, periodo=periodo_seleccionado),
                    to_attr='notas_filtradas'
                ),
                Prefetch(
                    'participaciones',
                    queryset=Participacion.objects.filter(
                        alumno=hijo, 
                        fecha__gte=timezone.now().date() - timedelta(days=90)
                    ).order_by('-fecha'),
                    to_attr='participaciones_filtradas'
                )
            )

            # Serializar asistencias para el contexto
            asistencias_serializadas = [
                {
                    'fecha': asistencia.fecha,
                    'presente': asistencia.presente,
                    'observaciones': asistencia.observaciones,
                    'hora_llegada': asistencia.hora_llegada,
                    'registrado_por_qr': asistencia.registrado_por_qr
                }
                for asistencia in asistencias
            ]

            # Construir el contexto completo para el serializer
            hijo_context = {
                'id': hijo.id,
                'nombre_completo': hijo.user.get_full_name(),
                'curso_nombre': hijo.curso.nombre,
                'nivel': hijo.curso.nivel,
                'periodo_actual': periodo_seleccionado,
                'periodos_disponibles': periodos_disponibles,
                'asistencias': asistencias_serializadas,
                'materias': materias,
                # Agregar información adicional del hijo
                'fecha_nacimiento': hijo.fecha_nacimiento,
                'grupo_sanguineo': hijo.grupo_sanguineo,
                'telefono_emergencia': hijo.telefono_emergencia
            }

            serializer = DetalleHijoSerializer(hijo_context, context={'request': request})
            
            # Enriquecer la respuesta con información adicional
            response_data = serializer.data
            response_data.update({
                'navegacion': self._generar_navegacion(hijo, padre),
                'comparacion_periodos': self._generar_comparacion_periodos(hijo, periodo_seleccionado, periodos_disponibles),
                'resumen_tendencias': self._generar_resumen_tendencias(hijo, periodos_disponibles)
            })
            
            return Response(response_data)

        except Padre.DoesNotExist:
            return Response({'error': 'Perfil de padre no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Alumno.DoesNotExist:
            return Response({'error': 'Hijo no encontrado o no tienes permiso para verlo.'}, status=status.HTTP_404_NOT_FOUND)
        except IndexError:
            return Response({'error': 'No hay períodos con notas disponibles para este alumno.'}, status=status.HTTP_404_NOT_FOUND)
    
    def _generar_navegacion(self, hijo, padre):
        """Generar información de navegación entre hermanos"""
        hermanos = padre.hijos.exclude(id=hijo.id).values('id', 'user__first_name', 'user__last_name', 'curso__nombre')
        
        return {
            'hermanos': list(hermanos),
            'es_hijo_unico': not hermanos.exists()
        }
    
    def _generar_comparacion_periodos(self, hijo, periodo_actual, periodos_disponibles):
        """Generar comparación entre períodos"""
        if len(periodos_disponibles) < 2:
            return None
        
        # Obtener notas del período actual y anterior
        notas_actual = Nota.objects.filter(alumno=hijo, periodo=periodo_actual).aggregate(
            promedio=Avg('valor'),
            total_notas=Count('id')
        )
        
        if len(periodos_disponibles) > 1:
            periodo_anterior = periodos_disponibles[1]
            notas_anterior = Nota.objects.filter(alumno=hijo, periodo=periodo_anterior).aggregate(
                promedio=Avg('valor'),
                total_notas=Count('id')
            )
            
            diferencia = None
            tendencia = 'estable'
            
            if notas_actual['promedio'] and notas_anterior['promedio']:
                diferencia = notas_actual['promedio'] - notas_anterior['promedio']
                if diferencia >= 3:
                    tendencia = 'mejorando'
                elif diferencia <= -3:
                    tendencia = 'empeorando'
            
            return {
                'periodo_anterior': periodo_anterior,
                'promedio_actual': round(notas_actual['promedio'], 1) if notas_actual['promedio'] else None,
                'promedio_anterior': round(notas_anterior['promedio'], 1) if notas_anterior['promedio'] else None,
                'diferencia': round(diferencia, 1) if diferencia else None,
                'tendencia': tendencia,
                'evaluaciones_actual': notas_actual['total_notas'],
                'evaluaciones_anterior': notas_anterior['total_notas']
            }
        
        return None
    
    def _generar_resumen_tendencias(self, hijo, periodos_disponibles):
        """Generar análisis de tendencias académicas"""
        if len(periodos_disponibles) < 3:
            return None
        
        # Obtener promedios de los últimos 3 períodos
        promedios_recientes = []
        for periodo in periodos_disponibles[:3]:
            promedio = Nota.objects.filter(
                alumno=hijo, 
                periodo=periodo
            ).aggregate(promedio=Avg('valor'))['promedio']
            
            if promedio:
                promedios_recientes.append({
                    'periodo': periodo,
                    'promedio': round(promedio, 1)
                })
        
        if len(promedios_recientes) >= 2:
            # Calcular tendencia general
            valores = [p['promedio'] for p in promedios_recientes]
            
            # Tendencia simple: comparar primer y último valor
            if valores[0] > valores[-1] + 2:
                tendencia_general = 'descendente'
            elif valores[0] < valores[-1] - 2:
                tendencia_general = 'ascendente'
            else:
                tendencia_general = 'estable'
            
            return {
                'tendencia_general': tendencia_general,
                'promedios_recientes': promedios_recientes,
                'mejor_periodo': max(promedios_recientes, key=lambda x: x['promedio']),
                'peor_periodo': min(promedios_recientes, key=lambda x: x['promedio'])
            }
        
        return None


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
