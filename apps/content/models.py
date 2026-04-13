from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=100, blank=True, help_text='Emoji or CSS icon class')
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('order', 'name')
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'

    def __str__(self):
        return self.name


class Book(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='books')
    grade = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(11)],
        help_text='School grade 1–11',
    )
    title = models.CharField(max_length=200)
    cover = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('grade', 'order')
        verbose_name = 'Book'
        verbose_name_plural = 'Books'

    def __str__(self):
        return f'{self.title} — Grade {self.grade}'


class Topic(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('order',)
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'

    def __str__(self):
        return f'{self.book} → {self.title}'


class Task(models.Model):
    class Type(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple_choice', 'Multiple Choice'
        OPEN_TEXT = 'open_text', 'Open Text'
        IMAGE_BASED = 'image_based', 'Image Based'
        FILL_BLANK = 'fill_blank', 'Fill in the Blank'

    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tasks')
    task_type = models.CharField(max_length=20, choices=Type.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    question = models.TextField()
    question_image = models.ImageField(
        upload_to='task_images/', blank=True, null=True,
        help_text='Required for image_based tasks.',
    )
    # ⚠ Never expose this field in any API serializer/response
    correct_answer = models.TextField(
        help_text='Stored server-side only. Must never appear in API responses.',
    )
    explanation = models.TextField(blank=True, help_text='Shown to student after the attempt.')
    points_reward = models.PositiveSmallIntegerField(default=10)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('order',)
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return f'[{self.get_task_type_display()}] {self.question[:70]}'


class TaskChoice(models.Model):
    """Answer options for multiple_choice and fill_blank tasks."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='choices')
    label = models.CharField(max_length=5, help_text='e.g. A, B, C, D')
    text = models.TextField()
    image = models.ImageField(upload_to='choice_images/', blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('order',)
        verbose_name = 'Task Choice'
        verbose_name_plural = 'Task Choices'

    def __str__(self):
        return f'{self.label}: {self.text[:50]}'
