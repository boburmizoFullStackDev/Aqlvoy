from django.db import models
from django.conf import settings


class AIChatConversation(models.Model):
    """Groups all messages belonging to a single chat context."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_conversations',
    )
    # Optional context link — AI can reference the topic being studied
    topic = models.ForeignKey(
        'content.Topic', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ai_conversations',
    )
    # Linked learning session — one session has one conversation
    session = models.OneToOneField(
        'learning_sessions.StudentSession',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ai_conversation',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-updated_at',)
        verbose_name = 'AI Conversation'
        verbose_name_plural = 'AI Conversations'

    def __str__(self):
        return f'Conv #{self.pk} — {self.user}'


class AIChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'

    class MessageType(models.TextChoices):
        TEXT = 'text', 'Text'
        IMAGE = 'image', 'Image'           # user sends a photo of a problem
        OCR_TEXT = 'ocr_text', 'OCR Text'  # extracted text from a photo
        AUDIO = 'audio', 'Audio'           # voice message
        ACTION = 'action', 'Action'        # AI returns a structured UI action

    conversation = models.ForeignKey(
        AIChatConversation, on_delete=models.CASCADE, related_name='messages',
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)

    # Primary content — present for text, ocr_text, and action messages
    text = models.TextField(blank=True)

    # Binary payload — present for image and audio messages
    media_file = models.FileField(upload_to='ai_chat/', blank=True, null=True)

    # Structured action payload (used when message_type = ACTION)
    # action_type examples: 'open_task', 'show_explanation', 'go_to_topic'
    action_type = models.CharField(max_length=50, blank=True)
    action_payload = models.JSONField(
        null=True, blank=True,
        help_text='Arbitrary JSON passed to the frontend to trigger a UI action.',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'AI Chat Message'
        verbose_name_plural = 'AI Chat Messages'

    def __str__(self):
        preview = (self.text[:50] or self.action_type or self.message_type)
        return f'[{self.role}:{self.message_type}] {preview}'
