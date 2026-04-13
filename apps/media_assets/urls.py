from django.urls import path
from . import views

app_name = 'media_assets'

urlpatterns = [
    path('',            views.asset_list,   name='asset-list'),
    path('upload/',     views.asset_upload, name='asset-upload'),
    path('<int:pk>/',   views.asset_detail, name='asset-detail'),
]
