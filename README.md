# Sistema de Información del Colegio - Backend

## 📋 Descripción

Sistema backend desarrollado en Django para la gestión integral de un colegio, que incluye manejo de alumnos, maestros, padres, notas, asistencia, participaciones y predicción de rendimiento académico.

## 🚀 Características Principales

### 🏫 Gestión Académica
- **Gestión de Alumnos**: CRUD completo de alumnos con relación a curso
- **Gestión de Maestros**: Maestros con rol de tutor por curso
- **Gestión de Cursos**: Cursos con materias asignadas
- **Gestión de Materias**: Materias específicas por curso

### 📊 Seguimiento Académico
- **Registro de Notas**: Por periodo, materia y alumno
- **Control de Asistencia**: Registro diario con soporte para QR
- **Participaciones**: Registro de participaciones en clase (escala 0-5)

### 👥 Gestión de Usuarios
- **Autenticación JWT**: Login seguro con tokens
- **Roles de Usuario**: Maestro, Alumno, Padre, Administrador
- **Permisos Granulares**: Acceso controlado por rol

### 📱 Asistencia por QR
- **Verificación de Ubicación**: Validación GPS del colegio
- **Control de Horario**: Horario específico para registro
- **Token de Colegio**: QR único por institución

### 🤖 Predicción de Rendimiento
- **Análisis Predictivo**: Basado en notas, asistencia y participaciones
- **Clasificación**: Alto, Medio, Bajo rendimiento
- **Variables**: Promedio histórico, asistencia, participaciones

## 🛠️ Tecnologías

- **Django 5.2.4**: Framework web principal
- **Django REST Framework**: API REST
- **JWT Authentication**: Autenticación con tokens
- **SQLite**: Base de datos (desarrollo)
- **Python 3.13**: Lenguaje de programación
- **Scikit-learn**: Machine Learning para predicciones

## ⚙️ Instalación

### Prerrequisitos
- Python 3.8+
- pip
- Virtual environment

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd colegio-backend
```

2. **Crear y activar entorno virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Aplicar migraciones**
```bash
python manage.py migrate
```

5. **Crear datos de prueba (opcional)**
```bash
python crear_datos_prueba.py
```

6. **Ejecutar servidor**
```bash
python manage.py runserver
```

## 🔗 Endpoints de la API

### Autenticación
- `POST /api/auth/login/` - Login (obtener JWT)
- `POST /api/auth/refresh/` - Refrescar token

### Gestión de Datos
- `GET|POST /api/colegios/` - Listar/crear colegios
- `GET|POST /api/maestros/` - Listar/crear maestros
- `GET|POST /api/cursos/` - Listar/crear cursos
- `GET|POST /api/materias/` - Listar/crear materias
- `GET|POST /api/alumnos/` - Listar/crear alumnos
- `GET|POST /api/padres/` - Listar/crear padres

### Seguimiento Académico
- `GET|POST /api/notas/` - Listar/crear notas
- `GET|POST /api/asistencia/` - Listar/crear asistencia
- `POST /api/asistencia/qr/` - Registrar asistencia por QR
- `GET|POST /api/participaciones/` - Listar/crear participaciones

### Predicción
- `GET /api/prediccion/{alumno_id}/{periodo}/` - Predicción de rendimiento

## 🔐 Sistema de Permisos

### Roles de Usuario

#### 👨‍🏫 Maestro Tutor
- ✅ Ver y gestionar su curso asignado
- ✅ Registrar notas de todas las materias de su curso
- ✅ Registrar asistencia de sus alumnos
- ✅ Registrar participaciones
- ❌ Acceder a otros cursos

#### 👨‍🎓 Alumno
- ✅ Ver sus propias notas
- ✅ Ver su asistencia
- ✅ Ver sus participaciones
- ✅ Registrar asistencia por QR
- ✅ Ver predicción de su rendimiento
- ❌ Ver información de otros alumnos

#### 👨‍👩‍👧‍👦 Padre
- ✅ Ver información de sus hijos
- ✅ Ver notas de sus hijos
- ✅ Ver asistencia de sus hijos
- ✅ Ver participaciones de sus hijos
- ✅ Ver predicción de rendimiento de sus hijos
- ❌ Acceder a información de otros alumnos

#### 👑 Administrador
- ✅ Acceso total al sistema
- ✅ Gestión de usuarios y datos
- ✅ Configuración del sistema

## 📱 Registro de Asistencia por QR

### Flujo de Funcionamiento

1. **Código QR del Colegio**: Cada colegio tiene un token QR único
2. **App Móvil**: Escanea el QR y envía:
   - Token del QR
   - Ubicación GPS del alumno
   - ID del alumno (desde sesión)

3. **Validaciones del Backend**:
   - ✅ Token QR válido para el colegio
   - ✅ Ubicación dentro del rango permitido
   - ✅ Horario escolar (7:00 - 8:30 AM por defecto)
   - ✅ Alumno autenticado

### Endpoint QR
```bash
POST /api/asistencia/qr/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
    "qr_token": "token_del_colegio",
    "latitud": -16.5000,
    "longitud": -68.1193
}
```

## 🤖 Predicción de Rendimiento

### Variables Utilizadas
1. **Promedio de Notas Anteriores**: Histórico del alumno
2. **Porcentaje de Asistencia**: Del periodo actual
3. **Promedio de Participaciones**: Del periodo actual

### Algoritmo
- Implementación actual: Promedio ponderado
- Futuro: Random Forest o Regresión Lineal
- Clasificación: Alto (≥85), Medio (70-84), Bajo (<70)

### Endpoint de Predicción
```bash
GET /api/prediccion/{alumno_id}/{periodo}/
Authorization: Bearer <jwt_token>
```

**Respuesta:**
```json
{
    "prediccion_numerica": 82.5,
    "clasificacion": "medio",
    "promedio_notas_anteriores": 78.5,
    "porcentaje_asistencia": 90.0,
    "promedio_participaciones": 4.2
}
```

## 💾 Datos de Prueba

El sistema incluye un script para generar datos de prueba:

### Usuarios Creados
- **Admin**: `admin/admin123`
- **Maestros**: `maestro1, maestro2, maestro3` / `maestro123`
- **Alumnos**: `alumno1-6` / `alumno123`
- **Padres**: `padre1-4` / `padre123`

### Datos Generados
- 1 Colegio (San José)
- 3 Cursos (1ro A, 2do A, 3ro A)
- 5 Materias por curso
- 6 Alumnos distribuidos en cursos
- Notas para 3 periodos (2024-T1, T2, T3)
- Asistencias de los últimos 30 días
- Participaciones aleatorias

## 🔧 Configuración

### Variables de Entorno (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=True
QR_ATTENDANCE_TIME_START=07:00
QR_ATTENDANCE_TIME_END=08:30
QR_LOCATION_TOLERANCE=0.001
```

### Configuración QR
- **Horario**: 7:00 - 8:30 AM (configurable)
- **Tolerancia GPS**: 0.001 grados (~100m)
- **Ubicación Colegio**: -16.5000, -68.1193

## 📊 Base de Datos

### Modelos Principales

```
Colegio
├── Curso (1:N)
│   ├── Maestro (tutor) (1:1)
│   ├── Alumno (1:N)
│   └── Materia (1:N)
│       ├── Nota (N:N con Alumno)
│       └── Participacion (N:N con Alumno)
├── Asistencia (1:N con Alumno)
└── Padre (N:N con Alumno)
```

### Relaciones Clave
- **1 Curso → 1 Maestro (tutor)**
- **1 Alumno → 1 Curso**
- **1 Curso → N Materias**
- **N Alumnos → N Padres**

## 🚀 Uso de la API

### Ejemplo de Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "maestro1", "password": "maestro123"}'
```

### Ejemplo de Consulta de Notas
```bash
curl -X GET http://localhost:8000/api/notas/?alumno=1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Ejemplo de Registro de Nota
```bash
curl -X POST http://localhost:8000/api/notas/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alumno": 1,
    "materia": 1,
    "periodo": "2024-T4",
    "valor": 85.5,
    "observaciones": "Excelente participación"
  }'
```

## 📈 Próximas Mejoras

- [ ] Implementación de ML avanzado para predicciones
- [ ] API para app móvil mejorada
- [ ] Notificaciones push
- [ ] Reportes en PDF
- [ ] Dashboard analítico
- [ ] Integración con sistemas de pago
- [ ] Chat entre padres y maestros
- [ ] Calendario académico

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 📞 Contacto

- Email: admin@colegio.com
- Documentación: `/admin/` para panel de administración
- API Root: `http://localhost:8000/`

---

**Desarrollado con ❤️ para la gestión educativa moderna** 