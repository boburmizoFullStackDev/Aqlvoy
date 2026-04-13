import json
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.content.models import Task, Topic
from apps.points.models import PointTransaction
from apps.users.decorators import jwt_required

from .models import StudentSession, TaskAttempt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


def _task_data(task):
    """Task payload — correct_answer intentionally excluded."""
    data = {
        'id':             task.id,
        'task_type':      task.task_type,
        'difficulty':     task.difficulty,
        'question':       task.question,
        'question_image': task.question_image.url if task.question_image else None,
        'points_reward':  task.points_reward,
        'order':          task.order,
        'choices':        [],
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


def _session_data(session):
    return {
        'id':            session.id,
        'topic_id':      session.topic_id,
        'topic_title':   session.topic.title if session.topic else None,
        'status':        session.status,
        'total_tasks':   session.total_tasks,
        'correct_count': session.correct_count,
        'score':         session.score,
        'started_at':    session.started_at.isoformat(),
        'completed_at':  session.completed_at.isoformat() if session.completed_at else None,
    }


def _attempt_data(attempt):
    return {
        'id':               attempt.id,
        'task_id':          attempt.task_id,
        'given_answer':     attempt.given_answer,
        'is_correct':       attempt.is_correct,
        'attempt_number':   attempt.attempt_number,
        'ai_help_used':     attempt.ai_help_used,
        'points_earned':    attempt.points_earned,
        'time_spent_seconds': attempt.time_spent_seconds,
        'attempted_at':     attempt.attempted_at.isoformat(),
    }


def _calc_points(base_points, attempt_number, ai_help_used):
    """
    Returns earned points based on attempt number and AI help flag.
      1st attempt  → 100 %
      2nd attempt  → 70 %
      3+ attempts  → 40 %
      AI help used → × 0.8
    Only called when the answer is correct.
    """
    if attempt_number == 1:
        multiplier = 1.0
    elif attempt_number == 2:
        multiplier = 0.7
    else:
        multiplier = 0.4

    if ai_help_used:
        multiplier *= 0.8

    return max(1, round(base_points * multiplier))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@csrf_exempt
@jwt_required
@require_GET
def session_list(request):
    """GET /api/v1/sessions/  — authenticated user's sessions, newest first."""
    sessions = (
        StudentSession.objects
        .filter(student=request.user)
        .select_related('topic')
    )
    return JsonResponse({'sessions': [_session_data(s) for s in sessions]})


@csrf_exempt
@jwt_required
@require_GET
def session_detail(request, pk):
    """GET /api/v1/sessions/<pk>/  — session + all attempts."""
    try:
        session = (
            StudentSession.objects
            .select_related('topic')
            .get(pk=pk, student=request.user)
        )
    except StudentSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found.'}, status=404)

    attempts = session.attempts.select_related('task').all()
    data = _session_data(session)
    data['attempts'] = [_attempt_data(a) for a in attempts]
    return JsonResponse(data)


@csrf_exempt
@jwt_required
@require_POST
def session_start(request):
    """
    POST /api/v1/sessions/start/
    Body: { "topic_id": <int> }

    Creates a new active session and returns the topic's published tasks.
    Rejects if an active session already exists for this topic.
    """
    d        = _json(request)
    topic_id = d.get('topic_id')

    if not topic_id:
        return JsonResponse({'error': 'topic_id is required.'}, status=400)

    try:
        topic = Topic.objects.prefetch_related('tasks__choices').get(
            pk=topic_id, is_published=True,
        )
    except Topic.DoesNotExist:
        return JsonResponse({'error': 'Topic not found.'}, status=404)

    # Prevent duplicate active sessions on the same topic
    if StudentSession.objects.filter(
        student=request.user, topic=topic, status=StudentSession.Status.ACTIVE,
    ).exists():
        return JsonResponse(
            {'error': 'You already have an active session for this topic.'},
            status=400,
        )

    tasks = list(topic.tasks.prefetch_related('choices').filter(is_published=True))

    session = StudentSession.objects.create(
        student=request.user,
        topic=topic,
        total_tasks=len(tasks),
    )

    return JsonResponse({
        'session': _session_data(session),
        'tasks':   [_task_data(t) for t in tasks],
    }, status=201)


@csrf_exempt
@jwt_required
@require_POST
def attempt_submit(request, session_pk):
    """
    POST /api/v1/sessions/<session_pk>/submit/
    Body: {
        "task_id":            <int>,
        "given_answer":       <str>,
        "time_spent_seconds": <int>   (optional, default 0),
        "ai_help_used":       <bool>  (optional, default false)
    }

    Scoring:
      - 1st attempt correct → 100 % of task.points_reward
      - 2nd attempt correct → 70 %
      - 3+ attempt correct  → 40 %
      - ai_help_used        → × 0.8
    Points only awarded on correct answers.
    """
    try:
        session = StudentSession.objects.select_related('student').get(
            pk=session_pk, student=request.user,
        )
    except StudentSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found.'}, status=404)

    if session.status != StudentSession.Status.ACTIVE:
        return JsonResponse(
            {'error': 'This session is no longer active.'},
            status=400,
        )

    d            = _json(request)
    task_id      = d.get('task_id')
    given_answer = d.get('given_answer')

    if not task_id or given_answer is None:
        return JsonResponse(
            {'error': 'task_id and given_answer are required.'},
            status=400,
        )

    # Task must belong to this session's topic
    try:
        task = Task.objects.get(pk=task_id, topic=session.topic, is_published=True)
    except Task.DoesNotExist:
        return JsonResponse(
            {'error': 'Task not found in this session\'s topic.'},
            status=404,
        )

    # Prevent submitting a task that was already answered correctly
    already_correct = session.attempts.filter(task=task, is_correct=True).exists()
    if already_correct:
        return JsonResponse(
            {'error': 'You have already answered this task correctly.'},
            status=400,
        )

    time_spent  = max(0, int(d.get('time_spent_seconds', 0) or 0))
    ai_help     = bool(d.get('ai_help_used', False))

    # Attempt number = all previous attempts for this task in this session + 1
    prior_count    = session.attempts.filter(task=task).count()
    attempt_number = prior_count + 1

    # Check correctness — case-insensitive, whitespace-stripped
    is_correct = (
        str(given_answer).strip().lower() ==
        str(task.correct_answer).strip().lower()
    )

    points_earned = 0
    if is_correct:
        points_earned = _calc_points(task.points_reward, attempt_number, ai_help)

    with transaction.atomic():
        attempt = TaskAttempt.objects.create(
            session=session,
            task=task,
            given_answer=str(given_answer),
            is_correct=is_correct,
            attempt_number=attempt_number,
            ai_help_used=ai_help,
            points_earned=points_earned,
            time_spent_seconds=time_spent,
        )

        if is_correct:
            # Update session counters
            session.correct_count += 1
            session.score         += points_earned
            session.save(update_fields=['correct_count', 'score'])

            # Update user total_points
            user = request.user
            user.total_points += points_earned
            user.save(update_fields=['total_points'])

            # Record point transaction
            PointTransaction.objects.create(
                user=user,
                delta=points_earned,
                source=PointTransaction.Source.TASK_CORRECT,
                balance_after=user.total_points,
                task_attempt=attempt,
            )

    return JsonResponse({
        'attempt':      _attempt_data(attempt),
        'is_correct':   is_correct,
        'points_earned': points_earned,
        'total_points': request.user.total_points,
        'session_score': session.score,
    }, status=201)


@csrf_exempt
@jwt_required
@require_POST
def session_complete(request, pk):
    """
    POST /api/v1/sessions/<pk>/complete/

    Marks the session as completed.
    Awards a small completion bonus if the student answered every task correctly.
    """
    try:
        session = StudentSession.objects.select_related('student').get(
            pk=pk, student=request.user,
        )
    except StudentSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found.'}, status=404)

    if session.status != StudentSession.Status.ACTIVE:
        return JsonResponse(
            {'error': 'Session is already completed or expired.'},
            status=400,
        )

    with transaction.atomic():
        session.status       = StudentSession.Status.COMPLETED
        session.completed_at = timezone.now()
        session.save(update_fields=['status', 'completed_at'])

        # Perfect score bonus: 20 % of total possible points
        bonus = 0
        if session.total_tasks > 0 and session.correct_count == session.total_tasks:
            max_points = (
                Task.objects
                .filter(topic=session.topic, is_published=True)
                .values_list('points_reward', flat=True)
            )
            bonus = round(sum(max_points) * 0.2)

            if bonus > 0:
                user = request.user
                user.total_points += bonus
                user.save(update_fields=['total_points'])

                PointTransaction.objects.create(
                    user=user,
                    delta=bonus,
                    source=PointTransaction.Source.SESSION_COMPLETE,
                    balance_after=user.total_points,
                    note=f'Perfect score bonus — session #{session.id}',
                )

    return JsonResponse({
        'session':      _session_data(session),
        'bonus_points': bonus,
        'total_points': request.user.total_points,
    })
