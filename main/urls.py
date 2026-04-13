from django.urls import path
from .views import index, login_page, register_page, student_page, teacher_page, parent_page

urlpatterns = [
    path('',          index,         name='index'),
    path('login/',    login_page,    name='login'),
    path('register/', register_page, name='register'),
    path('student/',  student_page,  name='student'),
    path('teacher/',  teacher_page,  name='teacher'),
    path('parent/',   parent_page,   name='parent'),
]
