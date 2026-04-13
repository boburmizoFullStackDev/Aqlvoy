from django.contrib import admin

from .models import StudentSession, TaskAttempt


class TaskAttemptInline(admin.TabularInline):
    model = TaskAttempt
    extra = 0
    readonly_fields = ('task', 'given_answer', 'is_correct', 'points_earned', 'time_spent_seconds', 'attempted_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StudentSession)
class StudentSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'topic', 'status', 'total_tasks', 'correct_count', 'score', 'started_at')
    list_filter = ('status', 'topic__book__subject', 'topic__book__grade')
    search_fields = ('student__phone', 'student__first_name')
    readonly_fields = ('started_at', 'completed_at', 'total_tasks', 'correct_count', 'score')
    inlines = (TaskAttemptInline,)
