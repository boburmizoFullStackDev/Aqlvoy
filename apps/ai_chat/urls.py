from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    path('chat/',                                         views.chat,                name='chat'),
    path('conversations/',                                views.conversation_list,   name='conversation-list'),
    path('conversations/<int:pk>/',                       views.conversation_detail, name='conversation-detail'),
    path('conversations/<int:conversation_pk>/messages/', views.message_create,      name='message-create'),
]
