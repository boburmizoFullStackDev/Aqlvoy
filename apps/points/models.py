from django.db import models
from django.conf import settings


class PointTransaction(models.Model):
    class Source(models.TextChoices):
        TASK_CORRECT = 'task_correct', 'Correct Answer'
        SESSION_COMPLETE = 'session_complete', 'Session Completed'
        DAILY_STREAK = 'daily_streak', 'Daily Streak'
        BONUS = 'bonus', 'Manual Bonus'
        DEDUCTION = 'deduction', 'Deduction'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='point_transactions',
    )
    delta = models.IntegerField(help_text='Positive = earned, negative = deducted.')
    source = models.CharField(max_length=30, choices=Source.choices)
    # Snapshot of balance immediately after this transaction
    balance_after = models.PositiveIntegerField(
        help_text='Value of user.total_points after this transaction was applied.',
    )
    # Optional hard link to the task attempt that triggered the transaction
    task_attempt = models.ForeignKey(
        'learning_sessions.TaskAttempt',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='point_transactions',
    )
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Point Transaction'
        verbose_name_plural = 'Point Transactions'

    def __str__(self):
        sign = '+' if self.delta >= 0 else ''
        return f'{self.user} {sign}{self.delta} [{self.source}] → {self.balance_after} pts'
