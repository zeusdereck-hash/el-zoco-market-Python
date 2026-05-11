from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# Importamos el sitio personalizado desde tu app tienda
from tienda.admin import admin_site 

urlpatterns = [
    # Reemplazamos el admin estándar por el personalizado de El Zoco
    path('admin/', admin_site.urls),
    path('', include('tienda.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)