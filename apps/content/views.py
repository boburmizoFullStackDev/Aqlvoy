from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from apps.users.decorators import jwt_required

from .models import Book, Subject, Task, TaskChoice, Topic


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------

def _subject_data(subject):
    return {
        'id':          subject.id,
        'name':        subject.name,
        'slug':        subject.slug,
        'icon':        subject.icon,
        'description': subject.description,
        'order':       subject.order,
    }


def _book_data(book):
    return {
        'id':           book.id,
        'subject_id':   book.subject_id,
        'subject_name': book.subject.name,
        'grade':        book.grade,
        'title':        book.title,
        'cover':        book.cover.url if book.cover else None,
        'description':  book.description,
        'order':        book.order,
    }


def _topic_data(topic):
    return {
        'id':          topic.id,
        'title':       topic.title,
        'description': topic.description,
        'order':       topic.order,
        'task_count':  topic.tasks.filter(is_published=True).count(),
    }


def _asset_data(asset):
    return {
        'id':         asset.id,
        'title':      asset.title,
        'asset_type': asset.asset_type,
        'url':        asset.file.url if asset.file else asset.external_url or None,
        'thumbnail':  asset.thumbnail.url if asset.thumbnail else None,
    }


def _task_data(task):
    """Task payload — correct_answer is intentionally excluded."""
    data = {
        'id':            task.id,
        'task_type':     task.task_type,
        'difficulty':    task.difficulty,
        'question':      task.question,
        'question_image': task.question_image.url if task.question_image else None,
        'points_reward': task.points_reward,
        'order':         task.order,
        'choices':       [],
    }
    if task.task_type in (Task.Type.MULTIPLE_CHOICE, Task.Type.FILL_BLANK):
        data['choices'] = [
            {
                'id':    c.id,
                'label': c.label,
                'text':  c.text,
                'image': c.image.url if c.image else None,
                'order': c.order,
            }
            for c in task.choices.all()
        ]
    return data


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@csrf_exempt
@jwt_required
@require_GET
def subject_list(request):
    """
    GET /api/v1/content/subjects/
    Optional filter: ?grade=<1-11>
    Returns subjects that have at least one published book for the given grade.
    Without ?grade, returns all subjects.
    """
    qs = Subject.objects.all()

    grade = request.GET.get('grade')
    if grade is not None:
        try:
            grade = int(grade)
            if not (1 <= grade <= 11):
                return JsonResponse({'error': 'grade must be between 1 and 11.'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'grade must be an integer.'}, status=400)
        qs = qs.filter(books__grade=grade, books__is_published=True).distinct()

    return JsonResponse({'subjects': [_subject_data(s) for s in qs]})


@csrf_exempt
@jwt_required
@require_GET
def book_list(request):
    """
    GET /api/v1/content/books/
    Optional filters: ?subject=<slug>  ?grade=<1-11>
    Returns only published books.
    """
    qs = Book.objects.select_related('subject').filter(is_published=True)

    subject_slug = request.GET.get('subject')
    if subject_slug:
        qs = qs.filter(subject__slug=subject_slug)

    grade = request.GET.get('grade')
    if grade is not None:
        try:
            grade = int(grade)
            if not (1 <= grade <= 11):
                return JsonResponse({'error': 'grade must be between 1 and 11.'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'grade must be an integer.'}, status=400)
        qs = qs.filter(grade=grade)

    return JsonResponse({'books': [_book_data(b) for b in qs]})


@csrf_exempt
@jwt_required
@require_GET
def book_detail(request, pk):
    """
    GET /api/v1/content/books/<pk>/
    Returns book info + list of published topics.
    """
    book = get_object_or_404(Book.objects.select_related('subject'), pk=pk, is_published=True)
    topics = book.topics.filter(is_published=True)
    data = _book_data(book)
    data['topics'] = [_topic_data(t) for t in topics]
    return JsonResponse(data)


@csrf_exempt
@jwt_required
@require_GET
def topic_detail(request, pk):
    """
    GET /api/v1/content/topics/<pk>/
    Returns topic info + attached media assets.
    """
    topic = get_object_or_404(
        Topic.objects.select_related('book__subject'),
        pk=pk,
        is_published=True,
    )
    data = {
        'id':          topic.id,
        'book_id':     topic.book_id,
        'book_title':  topic.book.title,
        'subject_id':  topic.book.subject_id,
        'subject_name': topic.book.subject.name,
        'title':       topic.title,
        'description': topic.description,
        'order':       topic.order,
        'task_count':  topic.tasks.filter(is_published=True).count(),
        'media_assets': [_asset_data(a) for a in topic.media_assets.all()],
    }
    return JsonResponse(data)


@csrf_exempt
@jwt_required
@require_GET
def topic_tasks(request, pk):
    """
    GET /api/v1/content/topics/<pk>/tasks/
    Optional filter: ?difficulty=easy|medium|hard
    Returns published tasks for the topic — correct_answer is never included.
    """
    topic = get_object_or_404(Topic, pk=pk, is_published=True)
    qs = topic.tasks.prefetch_related('choices').filter(is_published=True)

    difficulty = request.GET.get('difficulty')
    if difficulty:
        valid = {d.value for d in Task.Difficulty}
        if difficulty not in valid:
            return JsonResponse(
                {'error': f'difficulty must be one of: {", ".join(valid)}.'},
                status=400,
            )
        qs = qs.filter(difficulty=difficulty)

    return JsonResponse({'tasks': [_task_data(t) for t in qs]})


@csrf_exempt
@jwt_required
@require_GET
def task_detail(request, pk):
    """
    GET /api/v1/content/tasks/<pk>/
    Returns a single published task — correct_answer is never included.
    """
    task = get_object_or_404(
        Task.objects.prefetch_related('choices'),
        pk=pk,
        is_published=True,
    )
    return JsonResponse(_task_data(task))
