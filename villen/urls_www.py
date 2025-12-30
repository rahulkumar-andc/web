from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls), # Admin might be needed here too for some auth stuff, or not? 
    # Usually www has auth. 
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')), # This brings everything including blog/tools from core.urls if they are there.
    # We might want to redefine core.urls or filter things out, but for now this is the "www" view.
    
    path("instagram/", RedirectView.as_view(url="https://www.instagram.com/_vilen_bhai_", permanent=True)),
    path("github/", RedirectView.as_view(url="https://github.com/vilen-bhai", permanent=True)),
    path("linkedin/", RedirectView.as_view(url="https://www.linkedin.com/in/vilen-bhai", permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.custom_404_view'
handler500 = 'core.views.custom_500_view'
handler403 = 'core.views.custom_403_view'
handler400 = 'core.views.custom_400_view'
