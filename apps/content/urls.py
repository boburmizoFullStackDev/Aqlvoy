from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('subjects/',                  views.subject_list,  name='subject-list'),
    path('books/',                     views.book_list,     name='book-list'),
    path('books/<int:pk>/',            views.book_detail,   name='book-detail'),
    path('topics/<int:pk>/',           views.topic_detail,  name='topic-detail'),
    path('topics/<int:pk>/tasks/',     views.topic_tasks,   name='topic-tasks'),
    path('tasks/<int:pk>/',            views.task_detail,   name='task-detail'),
]
