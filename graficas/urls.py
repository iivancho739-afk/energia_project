from django.urls import path
from . import views

app_name = 'graficas'

urlpatterns = [
    path('', views.lista_conjuntos, name='lista'),
    path('cargar/', views.cargar_archivo, name='cargar'),
    path('conjunto/<int:conjunto_id>/', views.detalle_conjunto, name='detalle'),
    path('conjunto/<int:conjunto_id>/eliminar/', views.eliminar_conjunto, name='eliminar'),
]
