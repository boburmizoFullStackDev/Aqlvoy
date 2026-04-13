from django.contrib import admin

from .models import AIChatConversation, AIChatMessage


class AIChatMessageInline(admin.TabularInline):
    model = AIChatMessage
    extra = 0
    readonly_fields = ('role', 'message_type', 'text', 'media_file', 'action_type', 'action_payload', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(AIChatConversation)
class AIChatConversationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'topic', 'created_at', 'updated_at')
    list_filter = ('topic__book__subject',)
    search_fields = ('user__phone', 'user__first_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (AIChatMessageInline,)
