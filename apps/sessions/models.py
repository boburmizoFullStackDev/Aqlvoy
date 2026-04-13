from django.db import models
from django.conf import settings


class StudentSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        EXPIRED = 'expired', 'Expired'

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_sessions',
    )
    topic = models.ForeignKey(
        'content.Topic', on_delete=models.SET_NULL, null=True, related_name='student_sessions',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    total_tasks = models.PositiveSmallIntegerField(default=0)
    correct_count = models.PositiveSmallIntegerField(default=0)
    score = models.PositiveSmallIntegerField(default=0, help_text='Total points earned in this session.')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-started_at',)
        verbose_name = 'Student Session'
        verbose_name_plural = 'Student Sessions'

    def __str__(self):
        return f'{self.student} — {self.topic} [{self.status}]'


class TaskAttempt(models.Model):
    session = models.ForeignKey(StudentSession, on_delete=models.CASCADE, related_name='attempts')
    task = models.ForeignKey('content.Task', on_delete=models.CASCADE, related_name='attempts')
    given_answer = models.TextField()
    is_correct = models.BooleanField()
    attempt_number = models.PositiveSmallIntegerField(
        default=1,
        help_text='Which attempt this is for the task within the session (1 = first try).',
    )
    ai_help_used = models.BooleanField(
        default=False,
        help_text='If true, points are multiplied by 0.8.',
    )
    points_earned = models.PositiveSmallIntegerField(default=0)
    time_spent_seconds = models.PositiveSmallIntegerField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('attempted_at',)
        verbose_name = 'Task Attempt'
        verbose_name_plural = 'Task Attempts'

    def __str__(self):
        result = 'correct' if self.is_correct else 'wrong'
        return f'{self.session.student} → Task #{self.task_id} ({result})'
