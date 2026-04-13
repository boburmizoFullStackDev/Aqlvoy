from django.urls import path
from . import views

app_name = 'points'

urlpatterns = [
    path('',             views.point_history, name='history'),
    path('leaderboard/', views.leaderboard,   name='leaderboard'),
]
