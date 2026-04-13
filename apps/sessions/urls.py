from django.urls import path
from . import views

app_name = 'sessions'

urlpatterns = [
    path('',                                views.session_list,     name='session-list'),
    path('<int:pk>/',                       views.session_detail,   name='session-detail'),
    path('start/',                          views.session_start,    name='session-start'),
    path('<int:pk>/complete/',              views.session_complete, name='session-complete'),
    path('<int:session_pk>/submit/',        views.attempt_submit,   name='attempt-submit'),
]
