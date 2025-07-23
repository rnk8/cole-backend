from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # API Root
    path('', views.api_root, name='api-root'),
    
    # Autenticación
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Colegios
    path('colegios/', views.ColegioListCreateView.as_view(), name='colegio-list-create'),
    path('colegios/<int:pk>/', views.ColegioDetailView.as_view(), name='colegio-detail'),
    
    # Maestros
    path('maestros/', views.MaestroListCreateView.as_view(), name='maestro-list-create'),
    path('maestros/<int:pk>/', views.MaestroDetailView.as_view(), name='maestro-detail'),
    path('maestro/dashboard/', views.MaestroDashboardView.as_view(), name='maestro-dashboard'),
    
    # Cursos
    path('cursos/', views.CursoListCreateView.as_view(), name='curso-list-create'),
    path('cursos/<int:pk>/', views.CursoDetailView.as_view(), name='curso-detail'),
    
    # Materias
    path('materias/', views.MateriaListCreateView.as_view(), name='materia-list-create'),
    path('materias/<int:pk>/', views.MateriaDetailView.as_view(), name='materia-detail'),
    
    # Padres
    path('padres/', views.PadreListCreateView.as_view(), name='padre-list-create'),
    path('padres/<int:pk>/', views.PadreDetailView.as_view(), name='padre-detail'),
    
    # Alumnos
    path('alumnos/', views.AlumnoListCreateView.as_view(), name='alumno-list-create'),
    path('alumnos/<int:pk>/', views.AlumnoDetailView.as_view(), name='alumno-detail'),
    
    # Notas
    path('notas/', views.NotaListCreateView.as_view(), name='nota-list-create'),
    path('notas/<int:pk>/', views.NotaDetailView.as_view(), name='nota-detail'),
    
    # Asistencia
    path('asistencia/', views.AsistenciaListCreateView.as_view(), name='asistencia-list-create'),
    path('asistencia/<int:pk>/', views.AsistenciaDetailView.as_view(), name='asistencia-detail'),
    path('asistencia/qr/', views.QRAsistenciaView.as_view(), name='qr-asistencia'),
    
    # Participaciones
    path('participaciones/', views.ParticipacionListCreateView.as_view(), name='participacion-list-create'),
    path('participaciones/<int:pk>/', views.ParticipacionDetailView.as_view(), name='participacion-detail'),
    
    # Vistas para el Dashboard del Padre
    path('padre/dashboard/', views.PadreDashboardView.as_view(), name='padre-dashboard'),
    path('padre/hijo/<int:alumno_id>/', views.DetalleHijoView.as_view(), name='padre-hijo-detalle'),
    
    # Predicción de rendimiento
    path('prediccion/<int:alumno_id>/<str:periodo>/', views.PrediccionRendimientoView.as_view(), name='prediccion-rendimiento'),
] 