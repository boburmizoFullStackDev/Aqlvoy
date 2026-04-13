import json
import os
import uuid

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from openai import OpenAI

from apps.media_assets.models import MediaAsset
from apps.sessions.models import StudentSession
from apps.users.decorators import jwt_required

from .models import AIChatConversation, AIChatMessage


# ---------------------------------------------------------------------------
# OpenAI client — initialised once at module load
# ---------------------------------------------------------------------------

_openai = OpenAI(api_key=settings.OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# TTS voice mapping
# ---------------------------------------------------------------------------

_VOICE_MAP = {
    ('male',   'neutral'):   'onyx',
    ('male',   'warm'):      'echo',
    ('male',   'energetic'): 'fable',
    ('female', 'neutral'):   'nova',
    ('female', 'warm'):      'shimmer',
    ('female', 'energetic'): 'alloy',
}

_BOREDOM_KEYWORDS = {'zerikdim', 'charchadim', 'qiyin', 'tushunmadim'}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


def _get_voice(user):
    gender = getattr(user, 'character_gender', 'male')
    tone   = getattr(user, 'voice_tone', 'neutral')
    return _VOICE_MAP.get((gender, tone), 'onyx')


def _build_system_prompt(user, topic, task=None):
    """Dynamically builds an Uzbek-language teacher system prompt."""
    grade   = user.grade or 5
    subject = topic.book.subject.name if topic else "umumiy"
    topic_title = topic.title if topic else "mavzu"

    if grade <= 4:
        tone_desc = "juda sodda, qisqa gaplar bilan. 7-8 yoshli bola bilan gaplashayotgandek."
    elif grade <= 7:
        tone_desc = "o'rta murakkablikda, misollar bilan tushuntir."
    else:
        tone_desc = "batafsil va aniq tushuntir, formulalar va mantiqni ko'rsat."

    task_block = ""
    if task:
        task_block = f"""
Hozirgi topshiriq:
Savol: {task.question}
Topshiriq turi: {task.get_task_type_display()}
Qiyinlik: {task.get_difficulty_display()}

MUHIM: Hech qachon to'g'ri javobni to'g'ridan-to'g'ri aytma. Faqat bosqichma-bosqich yo'naltir.
"""

    return f"""Sen AQLVOY platformasining AI o'qituvchisissan.

O'quvchi haqida:
- Sinf: {grade}-sinf
- Fan: {subject}
- Mavzu: {topic_title}
{task_block}
Qoidalar:
1. FAQAT o'zbek tilida javob ber.
2. Hech qachon to'g'ri javobni to'g'ridan-to'g'ri berma — bosqichma-bosqich yo'nalt.
3. Ton: {tone_desc}
4. Qisqa, aniq va do'stona bo'l.
5. Agar o'quvchi charchagan yoki zerikkanga o'xshasa, uni rag'batlantirib, o'yinga taklif qil.

Javob formatini QATIY SAQ:
{{"message": "...", "action": "talking|thinking|celebrating|encouraging|pointing", "suggest_game": false, "mood_check": false}}

Faqat shu JSON formatida javob ber — boshqa hech narsa yozma."""


def _generate_audio(text, voice):
    """Call OpenAI TTS, save mp3, return relative URL or None on failure."""
    try:
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio', 'chat')
        os.makedirs(audio_dir, exist_ok=True)

        filename  = f"{uuid.uuid4().hex}.mp3"
        filepath  = os.path.join(audio_dir, filename)

        response = _openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text[:4096],          # TTS has a 4096 char limit
        )
        response.stream_to_file(filepath)
        return f"{settings.MEDIA_URL}audio/chat/{filename}"
    except Exception:
        return None


def _parse_ai_json(raw):
    """
    Safely parse the JSON object OpenAI returns.
    Returns (message, action, suggest_game, mood_check).
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # If OpenAI returns plain text despite instructions, wrap it
        data = {}

    message      = data.get('message') or raw or "Kechirasiz, qayta urinib ko'ring."
    action       = data.get('action', 'talking')
    suggest_game = bool(data.get('suggest_game', False))
    mood_check   = bool(data.get('mood_check', False))

    # Sanitise action value
    valid_actions = {'talking', 'thinking', 'celebrating', 'encouraging', 'pointing'}
    if action not in valid_actions:
        action = 'talking'

    return message, action, suggest_game, mood_check


def _asset_data(asset):
    return {
        'id':         asset.id,
        'title':      asset.title,
        'type':       asset.asset_type,
        'url':        asset.file.url if asset.file else asset.external_url or None,
        'thumbnail':  asset.thumbnail.url if asset.thumbnail else None,
    }


# ---------------------------------------------------------------------------
# Main chat endpoint
# ---------------------------------------------------------------------------

@csrf_exempt
@jwt_required
@require_POST
def chat(request):
    """
    POST /api/v1/ai-chat/chat/

    Body:
      {
        "session_id": int,
        "task_id":    int   (optional),
        "message":    str,
        "image_id":   int   (optional)
      }
    """
    d          = _json(request)
    session_id = d.get('session_id')
    task_id    = d.get('task_id')
    message    = (d.get('message') or '').strip()
    image_id   = d.get('image_id')

    if not message:
        return JsonResponse({'error': 'message is required.'}, status=400)

    # ── 1. Load session (optional — without it, AI has no topic context) ─
    session = None
    topic   = None
    if session_id:
        try:
            session = (
                StudentSession.objects
                .select_related('topic__book__subject')
                .get(pk=session_id, student=request.user)
            )
            topic = session.topic
        except StudentSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found.'}, status=404)

    # ── 2. Load optional task ────────────────────────────────────────────
    task = None
    if task_id:
        from apps.content.models import Task
        try:
            task = Task.objects.get(pk=task_id, topic=topic)
        except Task.DoesNotExist:
            pass

    # ── 3. Get or create conversation ────────────────────────────────────
    # With a session → one conversation per session.
    # Without a session → one general conversation per user (session=None).
    if session:
        conversation, _ = AIChatConversation.objects.get_or_create(
            session=session,
            defaults={'user': request.user, 'topic': topic},
        )
    else:
        conversation, _ = AIChatConversation.objects.get_or_create(
            user=request.user,
            session=None,
            topic=None,
        )

    # ── 4. Load last 10 messages (oldest first for context) ──────────────
    history = list(
        conversation.messages
        .order_by('created_at')
        .values('role', 'text', 'message_type')
        [:10]           # Django slicing gives first 10; re-order below
    )
    # Ensure we use the last 10, oldest-first
    history = list(
        conversation.messages
        .order_by('-created_at')
        .values('role', 'text', 'message_type')[:10]
    )
    history.reverse()

    # ── 5. OCR context ───────────────────────────────────────────────────
    user_message_text = message
    if image_id:
        try:
            img_msg = conversation.messages.get(pk=image_id)
            if img_msg.text:
                user_message_text += f"\n[Rasm matni: {img_msg.text}]"
        except AIChatMessage.DoesNotExist:
            pass

    # ── 6. Boredom / mood-check detection (backend logic) ────────────────
    words_lower   = set(message.lower().split())
    local_suggest_game = bool(words_lower & _BOREDOM_KEYWORDS)

    msg_count      = conversation.messages.count()
    local_mood_check = (msg_count > 0) and ((msg_count + 1) % 4 == 0)

    # ── 7. Build OpenAI messages list ────────────────────────────────────
    system_prompt = _build_system_prompt(request.user, topic, task)

    openai_messages = [{'role': 'system', 'content': system_prompt}]

    for h in history:
        role = h['role']        # 'user' or 'assistant'
        text = h['text']
        if text:
            openai_messages.append({'role': role, 'content': text})

    openai_messages.append({'role': 'user', 'content': user_message_text})

    # ── 8. Call OpenAI ───────────────────────────────────────────────────
    try:
        completion = _openai.chat.completions.create(
            model='gpt-4o-mini',
            messages=openai_messages,
            response_format={'type': 'json_object'},
            temperature=0.7,
            max_tokens=600,
        )
        raw_reply = completion.choices[0].message.content or ''
    except Exception as e:
        return JsonResponse(
            {'error': f'AI xizmati bilan bog\'lanishda xatolik: {str(e)}'},
            status=502,
        )

    # ── 9. Parse AI response ─────────────────────────────────────────────
    reply_text, action, ai_suggest_game, ai_mood_check = _parse_ai_json(raw_reply)

    suggest_game = local_suggest_game or ai_suggest_game
    mood_check   = local_mood_check   or ai_mood_check

    # ── 10. Generate TTS audio ───────────────────────────────────────────
    voice     = _get_voice(request.user)
    audio_url = _generate_audio(reply_text, voice)

    # ── 11. Persist messages ─────────────────────────────────────────────
    with transaction.atomic():
        # User message
        AIChatMessage.objects.create(
            conversation=conversation,
            role=AIChatMessage.Role.USER,
            message_type=AIChatMessage.MessageType.TEXT,
            text=user_message_text,
        )
        # Assistant response
        assistant_msg = AIChatMessage.objects.create(
            conversation=conversation,
            role=AIChatMessage.Role.ASSISTANT,
            message_type=AIChatMessage.MessageType.TEXT,
            text=reply_text,
            action_type=action,
            action_payload={
                'suggest_game': suggest_game,
                'mood_check':   mood_check,
                'audio_url':    audio_url,
            },
        )
        # Touch updated_at on conversation
        conversation.save(update_fields=['updated_at'])

    # ── 12. Game assets (if suggest_game) ────────────────────────────────
    game_assets = []
    if suggest_game and topic:
        assets = MediaAsset.objects.filter(topic=topic)[:3]
        game_assets = [_asset_data(a) for a in assets]

    # ── 13. Final response ───────────────────────────────────────────────
    return JsonResponse({
        'reply':        reply_text,
        'audio_url':    audio_url,
        'action':       action,
        'suggest_game': suggest_game,
        'mood_check':   mood_check,
        'game_assets':  game_assets,
    })


# ---------------------------------------------------------------------------
# Existing endpoints (conversation list / detail / message create)
# ---------------------------------------------------------------------------

@csrf_exempt
@jwt_required
@require_GET
def conversation_list(request):
    convs = (
        AIChatConversation.objects
        .filter(user=request.user)
        .select_related('topic', 'session')
        .order_by('-updated_at')
    )
    data = [
        {
            'id':         c.id,
            'topic_id':   c.topic_id,
            'topic_title': c.topic.title if c.topic else None,
            'session_id': c.session_id,
            'created_at': c.created_at.isoformat(),
            'updated_at': c.updated_at.isoformat(),
        }
        for c in convs
    ]
    return JsonResponse({'conversations': data})


@csrf_exempt
@jwt_required
@require_GET
def conversation_detail(request, pk):
    try:
        conv = AIChatConversation.objects.select_related('topic').get(
            pk=pk, user=request.user,
        )
    except AIChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found.'}, status=404)

    messages = [
        {
            'id':           m.id,
            'role':         m.role,
            'message_type': m.message_type,
            'text':         m.text,
            'action_type':  m.action_type,
            'action_payload': m.action_payload,
            'media_file':   m.media_file.url if m.media_file else None,
            'created_at':   m.created_at.isoformat(),
        }
        for m in conv.messages.order_by('created_at')
    ]
    return JsonResponse({
        'id':         conv.id,
        'topic_id':   conv.topic_id,
        'session_id': conv.session_id,
        'messages':   messages,
    })


@csrf_exempt
@jwt_required
def message_create(request, conversation_pk):
    """Legacy endpoint — kept for compatibility."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    if request.content_type and 'application/json' in request.content_type:
        d = _json(request)
    else:
        d = request.POST

    message_type = d.get('message_type', 'text')
    text         = d.get('text', '')
    media_file   = request.FILES.get('media_file')

    if message_type == 'text' and not text:
        return JsonResponse({'error': 'text is required for text messages.'}, status=400)
    if message_type in ('image', 'audio') and not media_file:
        return JsonResponse({'error': 'media_file is required for image/audio messages.'}, status=400)

    try:
        conv = AIChatConversation.objects.get(pk=conversation_pk, user=request.user)
    except AIChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found.'}, status=404)

    msg = AIChatMessage.objects.create(
        conversation=conv,
        role=AIChatMessage.Role.USER,
        message_type=message_type,
        text=text,
        media_file=media_file,
    )
    return JsonResponse({
        'id':           msg.id,
        'role':         msg.role,
        'message_type': msg.message_type,
        'text':         msg.text,
        'created_at':   msg.created_at.isoformat(),
    }, status=201)
