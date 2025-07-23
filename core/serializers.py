from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Colegio, Curso, Materia, Maestro, Alumno, Padre, 
    Nota, Asistencia, Participacion
)

class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password')
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class ColegioSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Colegio"""
    
    class Meta:
        model = Colegio
        fields = '__all__'
        read_only_fields = ('token_qr',)

class MaestroSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Maestro"""
    user = UserSerializer()
    
    class Meta:
        model = Maestro
        fields = '__all__'
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        maestro = Maestro.objects.create(user=user, **validated_data)
        return maestro

class MaestroListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de maestros"""
    nombre_completo = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Maestro
        fields = ('id', 'nombre_completo', 'username', 'telefono')
    
    def get_nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

class CursoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Curso"""
    tutor_nombre = serializers.CharField(source='tutor.user.get_full_name', read_only=True)
    colegio_nombre = serializers.CharField(source='colegio.nombre', read_only=True)
    num_alumnos = serializers.SerializerMethodField()
    
    class Meta:
        model = Curso
        fields = '__all__'
    
    def get_num_alumnos(self, obj):
        return obj.alumnos.count()

class MateriaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Materia"""
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    
    class Meta:
        model = Materia
        fields = '__all__'

class PadreSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Padre"""
    user = UserSerializer()
    hijos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Padre
        fields = '__all__'
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        padre = Padre.objects.create(user=user, **validated_data)
        return padre
    
    def get_hijos_count(self, obj):
        return obj.hijos.count()

class AlumnoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Alumno"""
    user = UserSerializer()
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    padres_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Alumno
        fields = '__all__'
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        padres_data = validated_data.pop('padres', [])
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        alumno = Alumno.objects.create(user=user, **validated_data)
        if padres_data:
            alumno.padres.set(padres_data)
        return alumno
    
    def get_padres_info(self, obj):
        return [f"{padre.user.first_name} {padre.user.last_name}" for padre in obj.padres.all()]

class AlumnoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listas de alumnos"""
    nombre_completo = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    
    class Meta:
        model = Alumno
        fields = ('id', 'nombre_completo', 'username', 'curso_nombre', 'fecha_nacimiento')
    
    def get_nombre_completo(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

class NotaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Nota"""
    alumno_nombre = serializers.CharField(source='alumno.user.get_full_name', read_only=True)
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    
    class Meta:
        model = Nota
        fields = '__all__'
    
    def validate_valor(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("La nota debe estar entre 0 y 100")
        return value

class AsistenciaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Asistencia"""
    alumno_nombre = serializers.CharField(source='alumno.user.get_full_name', read_only=True)
    
    class Meta:
        model = Asistencia
        fields = '__all__'
        read_only_fields = ('fecha_registro', 'registrado_por_qr')

class QRAsistenciaSerializer(serializers.Serializer):
    """Serializer para el registro de asistencia por QR"""
    qr_token = serializers.CharField(max_length=100)
    latitud = serializers.FloatField()
    longitud = serializers.FloatField()

class ParticipacionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Participacion"""
    alumno_nombre = serializers.CharField(source='alumno.user.get_full_name', read_only=True)
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    
    class Meta:
        model = Participacion
        fields = '__all__'
    
    def validate_valor(self, value):
        if value < 0 or value > 5:
            raise serializers.ValidationError("La participación debe estar entre 0 y 5")
        return value

# --- Serializers para el Dashboard del Padre ---

class HijoDashboardSerializer(serializers.ModelSerializer):
    """Serializer mejorado para mostrar un resumen completo de cada hijo en el dashboard del padre."""
    nombre_completo = serializers.CharField(source='user.get_full_name', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    nivel = serializers.CharField(source='curso.nivel', read_only=True)
    foto_url = serializers.SerializerMethodField()
    
    # Estadísticas académicas
    promedio_periodo = serializers.FloatField(read_only=True)
    promedio_anterior = serializers.FloatField(read_only=True)
    tendencia_academica = serializers.SerializerMethodField()
    
    # Estadísticas de asistencia
    porcentaje_asistencia = serializers.FloatField(read_only=True)
    dias_ausente_mes = serializers.IntegerField(read_only=True)
    
    # Estadísticas de participación
    total_participaciones_mes = serializers.IntegerField(read_only=True)
    promedio_participaciones = serializers.FloatField(read_only=True)
    
    # Alertas y estado
    alertas = serializers.SerializerMethodField()
    estado_academico = serializers.SerializerMethodField()
    
    # Próximos eventos (simulado)
    proximos_eventos = serializers.SerializerMethodField()

    class Meta:
        model = Alumno
        fields = (
            'id', 'nombre_completo', 'curso_nombre', 'nivel', 'foto_url',
            'promedio_periodo', 'promedio_anterior', 'tendencia_academica',
            'porcentaje_asistencia', 'dias_ausente_mes',
            'total_participaciones_mes', 'promedio_participaciones',
            'alertas', 'estado_academico', 'proximos_eventos'
        )
    
    def get_foto_url(self, obj):
        return f"https://i.pravatar.cc/150?u={obj.user.username}"
    
    def get_tendencia_academica(self, obj):
        """Calcular tendencia académica comparando períodos"""
        promedio_actual = getattr(obj, 'promedio_periodo', None)
        promedio_anterior = getattr(obj, 'promedio_anterior', None)
        
        if promedio_actual is None or promedio_anterior is None:
            return 'neutro'
        
        diferencia = promedio_actual - promedio_anterior
        if diferencia >= 5:
            return 'mejorando'
        elif diferencia <= -5:
            return 'empeorando'
        else:
            return 'estable'
    
    def get_alertas(self, obj):
        """Generar alertas basadas en el rendimiento del alumno"""
        alertas = []
        
        # Alerta por baja asistencia
        if hasattr(obj, 'porcentaje_asistencia') and obj.porcentaje_asistencia is not None:
            if obj.porcentaje_asistencia < 80:
                alertas.append({
                    'tipo': 'asistencia',
                    'nivel': 'warning' if obj.porcentaje_asistencia >= 70 else 'danger',
                    'mensaje': f'Asistencia baja: {obj.porcentaje_asistencia:.0f}%',
                    'icono': 'calendar-x'
                })
        
        # Alerta por bajo rendimiento académico
        if hasattr(obj, 'promedio_periodo') and obj.promedio_periodo is not None:
            if obj.promedio_periodo < 60:
                alertas.append({
                    'tipo': 'academico',
                    'nivel': 'danger',
                    'mensaje': f'Promedio bajo: {obj.promedio_periodo:.1f}',
                    'icono': 'trending-down'
                })
            elif obj.promedio_periodo < 70:
                alertas.append({
                    'tipo': 'academico',
                    'nivel': 'warning',
                    'mensaje': f'Promedio necesita atención: {obj.promedio_periodo:.1f}',
                    'icono': 'alert-triangle'
                })
        
        # Alerta por tendencia negativa
        tendencia = self.get_tendencia_academica(obj)
        if tendencia == 'empeorando':
            alertas.append({
                'tipo': 'tendencia',
                'nivel': 'warning',
                'mensaje': 'Tendencia académica descendente',
                'icono': 'trending-down'
            })
        
        return alertas
    
    def get_estado_academico(self, obj):
        """Determinar el estado académico general"""
        promedio = getattr(obj, 'promedio_periodo', None)
        asistencia = getattr(obj, 'porcentaje_asistencia', None)
        
        if promedio is None:
            return 'sin_datos'
        
        if promedio >= 85 and (asistencia is None or asistencia >= 90):
            return 'excelente'
        elif promedio >= 70 and (asistencia is None or asistencia >= 80):
            return 'bueno'
        elif promedio >= 60 and (asistencia is None or asistencia >= 70):
            return 'regular'
        else:
            return 'necesita_atencion'
    
    def get_proximos_eventos(self, obj):
        """Simular próximos eventos (en una implementación real vendría de la BD)"""
        import random
        eventos = [
            'Entrega de proyecto de Ciencias',
            'Examen de Matemáticas',
            'Presentación oral de Historia',
            'Evaluación de Educación Física',
            'Feria de Ciencias'
        ]
        
        # Simular 0-2 eventos próximos
        num_eventos = random.randint(0, 2)
        if num_eventos == 0:
            return []
        
        return [
            {
                'titulo': random.choice(eventos),
                'fecha': '2024-12-15',  # En una implementación real sería dinámico
                'tipo': random.choice(['examen', 'proyecto', 'presentacion'])
            }
            for _ in range(num_eventos)
        ]

class NotaPadreSerializer(serializers.ModelSerializer):
    """Serializer simplificado de notas para la vista del padre."""
    class Meta:
        model = Nota
        fields = ('valor', 'observaciones', 'fecha_registro')

class AsistenciaPadreSerializer(serializers.ModelSerializer):
    """Serializer simplificado de asistencias para la vista del padre."""
    class Meta:
        model = Asistencia
        fields = ('fecha', 'presente', 'observaciones')

class ParticipacionPadreSerializer(serializers.ModelSerializer):
    """Serializer simplificado de participaciones para la vista del padre."""
    class Meta:
        model = Participacion
        fields = ('fecha', 'valor', 'tipo_participacion', 'observaciones')

class MateriaConDetalleSerializer(serializers.Serializer):
    """Serializer para una materia con sus notas, asistencias y participaciones asociadas."""
    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    notas = NotaPadreSerializer(many=True, read_only=True)
    participaciones = ParticipacionPadreSerializer(many=True, read_only=True)


class DetalleHijoSerializer(serializers.Serializer):
    """Serializer mejorado para la vista de detalle de un hijo, con toda su información académica."""
    id = serializers.IntegerField(read_only=True)
    nombre_completo = serializers.CharField(read_only=True)
    curso_nombre = serializers.CharField(read_only=True)
    nivel = serializers.CharField(read_only=True)
    
    # Información del período actual
    periodo_actual = serializers.CharField(read_only=True)
    periodos_disponibles = serializers.ListField(child=serializers.CharField(), read_only=True)
    
    # Estadísticas del período
    estadisticas_periodo = serializers.SerializerMethodField()
    
    # Datos detallados
    asistencias = AsistenciaPadreSerializer(many=True, read_only=True)
    materias = MateriaConDetalleSerializer(many=True, read_only=True)
    
    # Análisis y recomendaciones
    analisis_rendimiento = serializers.SerializerMethodField()
    recomendaciones = serializers.SerializerMethodField()
    
    def get_estadisticas_periodo(self, obj):
        """Calcular estadísticas completas del período"""
        materias = obj.get('materias', [])
        asistencias = obj.get('asistencias', [])
        
        # Calcular promedios por materia
        promedios_materias = []
        promedio_general = 0
        total_materias_con_notas = 0
        
        for materia in materias:
            notas = getattr(materia, 'notas_filtradas', [])
            if notas:
                promedio_materia = sum(nota.valor for nota in notas) / len(notas)
                promedios_materias.append({
                    'materia': materia.nombre,
                    'promedio': round(promedio_materia, 1),
                    'num_evaluaciones': len(notas)
                })
                promedio_general += promedio_materia
                total_materias_con_notas += 1
        
        promedio_general = round(promedio_general / total_materias_con_notas, 1) if total_materias_con_notas > 0 else None
        
        # Calcular estadísticas de asistencia
        total_dias = len(asistencias)
        dias_presente = sum(1 for a in asistencias if a['presente'])
        porcentaje_asistencia = round((dias_presente / total_dias) * 100, 1) if total_dias > 0 else 100
        
        # Calcular participaciones
        total_participaciones = sum(
            len(getattr(materia, 'participaciones_filtradas', []))
            for materia in materias
        )
        
        return {
            'promedio_general': promedio_general,
            'promedios_por_materia': promedios_materias,
            'porcentaje_asistencia': porcentaje_asistencia,
            'dias_presente': dias_presente,
            'total_dias': total_dias,
            'total_participaciones': total_participaciones,
            'materias_con_notas': total_materias_con_notas,
            'total_materias': len(materias)
        }
    
    def get_analisis_rendimiento(self, obj):
        """Generar análisis del rendimiento académico"""
        estadisticas = self.get_estadisticas_periodo(obj)
        promedio = estadisticas['promedio_general']
        asistencia = estadisticas['porcentaje_asistencia']
        
        analisis = {
            'nivel_academico': 'sin_datos',
            'nivel_asistencia': 'excelente',
            'materias_destacadas': [],
            'materias_atencion': [],
            'tendencia_general': 'estable'
        }
        
        # Análisis académico
        if promedio is not None:
            if promedio >= 85:
                analisis['nivel_academico'] = 'excelente'
            elif promedio >= 75:
                analisis['nivel_academico'] = 'bueno'
            elif promedio >= 65:
                analisis['nivel_academico'] = 'regular'
            else:
                analisis['nivel_academico'] = 'necesita_mejora'
        
        # Análisis de asistencia
        if asistencia >= 95:
            analisis['nivel_asistencia'] = 'excelente'
        elif asistencia >= 85:
            analisis['nivel_asistencia'] = 'bueno'
        elif asistencia >= 75:
            analisis['nivel_asistencia'] = 'regular'
        else:
            analisis['nivel_asistencia'] = 'preocupante'
        
        # Identificar materias destacadas y que necesitan atención
        promedios_materias = estadisticas['promedios_por_materia']
        if promedios_materias:
            materias_ordenadas = sorted(promedios_materias, key=lambda x: x['promedio'], reverse=True)
            
            # Materias destacadas (top 2 con promedio >= 80)
            analisis['materias_destacadas'] = [
                m for m in materias_ordenadas[:2] if m['promedio'] >= 80
            ]
            
            # Materias que necesitan atención (promedio < 70)
            analisis['materias_atencion'] = [
                m for m in materias_ordenadas if m['promedio'] < 70
            ]
        
        return analisis
    
    def get_recomendaciones(self, obj):
        """Generar recomendaciones personalizadas"""
        analisis = self.get_analisis_rendimiento(obj)
        estadisticas = self.get_estadisticas_periodo(obj)
        recomendaciones = []
        
        # Recomendaciones académicas
        if analisis['nivel_academico'] == 'necesita_mejora':
            recomendaciones.append({
                'tipo': 'academico',
                'prioridad': 'alta',
                'titulo': 'Refuerzo académico necesario',
                'descripcion': 'Considere programar sesiones de estudio adicionales',
                'icono': 'book-open'
            })
        
        # Recomendaciones de asistencia
        if analisis['nivel_asistencia'] in ['regular', 'preocupante']:
            recomendaciones.append({
                'tipo': 'asistencia',
                'prioridad': 'alta' if analisis['nivel_asistencia'] == 'preocupante' else 'media',
                'titulo': 'Mejorar asistencia',
                'descripcion': f'La asistencia del {estadisticas["porcentaje_asistencia"]}% puede afectar el rendimiento',
                'icono': 'calendar-check'
            })
        
        # Recomendaciones por materias específicas
        if analisis['materias_atencion']:
            materia_problema = analisis['materias_atencion'][0]
            recomendaciones.append({
                'tipo': 'materia_especifica',
                'prioridad': 'media',
                'titulo': f'Apoyo en {materia_problema["materia"]}',
                'descripcion': f'Promedio de {materia_problema["promedio"]} necesita atención',
                'icono': 'alert-triangle'
            })
        
        # Recomendaciones de participación
        if estadisticas['total_participaciones'] < 5:
            recomendaciones.append({
                'tipo': 'participacion',
                'prioridad': 'baja',
                'titulo': 'Fomentar participación',
                'descripcion': 'Anime a su hijo a participar más en clase',
                'icono': 'message-square'
            })
        
        return recomendaciones




# --- Serializers para el Dashboard del Maestro ---

class NotaMaestroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = ('id', 'materia', 'valor', 'periodo', 'fecha_registro')

class ParticipacionMaestroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participacion
        fields = ('id', 'materia', 'valor', 'fecha')

class AlumnoParaMaestroSerializer(serializers.ModelSerializer):
    """Serializer de un alumno para la vista de gestión del maestro tutor."""
    nombre_completo = serializers.CharField(source='user.get_full_name', read_only=True)
    notas = serializers.SerializerMethodField()
    participaciones = ParticipacionMaestroSerializer(many=True, read_only=True)
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model = Alumno
        fields = ('id', 'nombre_completo', 'foto_url', 'notas', 'participaciones')

    def get_notas(self, obj):
        # Try to get filtered notes first, fall back to all notes
        if hasattr(obj, 'notas_filtradas'):
            return NotaMaestroSerializer(obj.notas_filtradas, many=True).data
        else:
            return NotaMaestroSerializer(obj.notas.all(), many=True).data

    def get_foto_url(self, obj):
        return f"https://i.pravatar.cc/150?u={obj.user.username}"

class MaestroDashboardSerializer(serializers.Serializer):
    """Serializer para el endpoint principal del dashboard del maestro."""
    curso = CursoSerializer()
    materias = MateriaSerializer(many=True)
    alumnos = AlumnoParaMaestroSerializer(many=True)
    periodos = serializers.ListField(child=serializers.CharField())


class PrediccionSerializer(serializers.Serializer):
    """Serializer para la respuesta de predicción de rendimiento"""
    prediccion_numerica = serializers.FloatField()
    clasificacion = serializers.CharField()
    promedio_notas_anteriores = serializers.FloatField()
    porcentaje_asistencia = serializers.FloatField()
    promedio_participaciones = serializers.FloatField() 