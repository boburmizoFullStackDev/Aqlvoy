from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

API_V1 = 'api/v1/'

urlpatterns = [
    path('', include('main.urls')),
    path('admin/', admin.site.urls),

    # Auth endpoints (register, login, logout)
    path('api/auth/', include('apps.users.auth_urls')),

    # App routers
    path(API_V1 + 'users/', include('apps.users.urls', namespace='users')),
    path(API_V1 + 'content/', include('apps.content.urls', namespace='content')),
    path(API_V1 + 'sessions/', include('apps.sessions.urls', namespace='sessions')),
    path(API_V1 + 'ai-chat/', include('apps.ai_chat.urls', namespace='ai_chat')),
    path(API_V1 + 'points/', include('apps.points.urls', namespace='points')),
    path(API_V1 + 'media-assets/', include('apps.media_assets.urls', namespace='media_assets')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
