from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("new", views.create_paste, name="create_paste"),
    path('ads.txt', views.ads_txt, name='ads_txt'),
    path("advtest", views.advtest, name="advtest"),
    path("contact", views.contact, name="contact"),
    path("pricing, views.pricing, name="pricing"),
    path("terms", views.terms, name="terms"),
    path('p/<str:paste_id>/', views.view_paste, name='view_paste'),
    path('p/<str:paste_id>/raw/', views.raw_paste, name='raw_paste'),
    path('p/<str:paste_id>/clone/', views.clone_paste, name='clone_paste'),
]
