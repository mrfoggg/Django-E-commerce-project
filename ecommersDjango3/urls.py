from baton.autodiscover import admin
import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

admin.site.site_header = 'Интернет магазин "Снип-Сноп"'
admin.site.site_title = "Снип-Сноп"
admin.site.index_title = "Снип-Сноп администрирование"

urlpatterns = [
    path('', include('home.urls')),
    path('products/', include('products.urls')),
    path('_nested_admin/', include('nested_admin.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('admin/', admin.site.urls),
    path('baton/', include('baton.urls')),
    path('__debug__/', include(debug_toolbar.urls)),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         path('__debug__/', include(debug_toolbar.urls)),
#
#         # For django versions before 2.0:
#         # url(r'^__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns