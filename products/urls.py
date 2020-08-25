from django.contrib import  admin
from django.urls import re_path, path, include
from .views import CategoryView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('<slug:category_slug>/', CategoryView.as_view(), name='category'),
    path('summernote/', include('django_summernote.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)