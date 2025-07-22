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

class PrediccionSerializer(serializers.Serializer):
    """Serializer para la respuesta de predicción de rendimiento"""
    prediccion_numerica = serializers.FloatField()
    clasificacion = serializers.CharField()
    promedio_notas_anteriores = serializers.FloatField()
    porcentaje_asistencia = serializers.FloatField()
    promedio_participaciones = serializers.FloatField() 