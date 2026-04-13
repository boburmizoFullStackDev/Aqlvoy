from django.contrib import admin

from .models import Subject, Book, Topic, Task, TaskChoice


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = ('title', 'order', 'is_published')
    ordering = ('order',)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'grade', 'is_published', 'order', 'created_at')
    list_filter = ('subject', 'grade', 'is_published')
    search_fields = ('title',)
    ordering = ('grade', 'order')
    inlines = (TopicInline,)


class TaskChoiceInline(admin.TabularInline):
    model = TaskChoice
    extra = 4
    fields = ('label', 'text', 'image', 'order')
    ordering = ('order',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'book', 'order', 'is_published', 'created_at')
    list_filter = ('book__subject', 'book__grade', 'is_published')
    search_fields = ('title',)
    ordering = ('book__grade', 'book__order', 'order')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('short_question', 'topic', 'task_type', 'difficulty', 'points_reward', 'is_published', 'order')
    list_filter = ('task_type', 'difficulty', 'is_published', 'topic__book__grade', 'topic__book__subject')
    search_fields = ('question',)
    ordering = ('topic', 'order')
    inlines = (TaskChoiceInline,)

    # Ensure correct_answer is only visible in admin, never exposed elsewhere
    fieldsets = (
        (None, {'fields': ('topic', 'task_type', 'difficulty', 'order', 'is_published')}),
        ('Question', {'fields': ('question', 'question_image')}),
        ('Answer (server-side only)', {
            'fields': ('correct_answer', 'explanation'),
            'classes': ('collapse',),
            'description': '⚠ Never expose correct_answer in API responses.',
        }),
        ('Scoring', {'fields': ('points_reward',)}),
    )

    def short_question(self, obj):
        return obj.question[:60]
    short_question.short_description = 'Question'
