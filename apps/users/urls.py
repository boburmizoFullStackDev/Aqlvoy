from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('me/',                 views.profile,        name='profile'),
    path('me/stats/',           views.student_stats,  name='stats'),
    path('leaderboard/',        views.leaderboard,    name='leaderboard'),
    path('children/',           views.children,       name='children'),
    path('children/<int:pk>/',  views.child_remove,   name='child-remove'),
]
