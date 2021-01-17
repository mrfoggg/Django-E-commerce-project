from django.urls import include, path, re_path

from home import views

urlpatterns = [
    path('', views.index, name='home'),
]
