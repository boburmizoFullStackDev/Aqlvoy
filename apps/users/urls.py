from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('me/',                 views.profile,      name='profile'),
    path('children/',           views.children,     name='children'),
    path('children/<int:pk>/',  views.child_remove, name='child-remove'),
]
