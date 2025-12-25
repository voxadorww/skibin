from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("new", views.create_paste, name="create_paste"),
    path("contact", views.contact, name="contact"),
    path("terms", views.terms, name="terms"),
    path('status/', views.status_page, name='status'),
    path('api/health/', views.health_check, name='health_check'),
    path('api/db-health/', views.db_health, name='db_health'),
    path('api/status/', views.status_data, name='status_data'),
    path('p/<str:paste_id>/', views.view_paste, name='view_paste'),
    path('p/<str:paste_id>/raw/', views.raw_paste, name='raw_paste'),
    path('p/<str:paste_id>/clone/', views.clone_paste, name='clone_paste'),
]
