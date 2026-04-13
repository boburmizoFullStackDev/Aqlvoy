import json
import re

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .decorators import jwt_required
from .models import User

PHONE_RE = re.compile(r'^\+?[1-9]\d{8,14}$')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_payload(user):
    return {
        'id':           user.id,
        'name':         user.full_name or user.first_name,
        'phone':        user.phone,
        'role':         user.role,
        'grade':        user.grade,
        'total_points': user.total_points,
        'avatar':       user.avatar.url if user.avatar else None,
    }


def _jwt(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def _json(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# Auth  — /api/auth/
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    d        = _json(request)
    phone    = d.get('phone', '').strip()
    name     = d.get('name', '').strip()
    password = d.get('password', '')
    role     = d.get('role', '').strip()
    errors   = {}

    if not phone:
        errors['phone'] = "Telefon raqam kiritish shart."
    elif not PHONE_RE.match(phone):
        errors['phone'] = "Noto'g'ri format. Masalan: +998901234567"
    elif User.objects.filter(phone=phone).exists():
        errors['phone'] = "Bu raqam allaqachon ro'yxatdan o'tgan."

    if not name:
        errors['name'] = "Ism kiritish shart."

    if not password:
        errors['password'] = "Parol kiritish shart."
    elif len(password) < 6:
        errors['password'] = "Parol kamida 6 ta belgi bo'lishi kerak."

    valid_roles = {r.value for r in User.Role}
    if not role:
        errors['role'] = "Rolni tanlang."
    elif role not in valid_roles:
        errors['role'] = f"Noto'g'ri rol. Mumkin: {', '.join(valid_roles)}"

    grade = None
    if role == User.Role.STUDENT and 'role' not in errors:
        raw = d.get('student_class') or d.get('grade')
        if raw:
            m = re.search(r'\d+', str(raw))
            grade = int(m.group()) if m else None
        if grade is None or not (1 <= grade <= 11):
            errors['grade'] = "Sinf 1 dan 11 gacha bo'lishi kerak."

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    parts = name.split(maxsplit=1)
    user = User.objects.create_user(
        phone=phone,
        password=password,
        first_name=parts[0],
        last_name=parts[1] if len(parts) > 1 else '',
        role=role,
        grade=grade,
    )
    return JsonResponse({'user': _user_payload(user), **_jwt(user)}, status=201)


@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    d        = _json(request)
    phone    = d.get('phone', '').strip()
    password = d.get('password', '')

    if not phone or not password:
        return JsonResponse(
            {'detail': "Telefon raqam va parol kiritish shart."},
            status=400,
        )

    user = authenticate(request, phone=phone, password=password)
    if user is None:
        return JsonResponse(
            {'detail': "Telefon raqam yoki parol noto'g'ri."},
            status=401,
        )
    if not user.is_active:
        return JsonResponse(
            {'detail': "Hisobingiz faol emas."},
            status=403,
        )
    return JsonResponse({'user': _user_payload(user), **_jwt(user)})


@csrf_exempt
@require_http_methods(['POST'])
def logout(request):
    d             = _json(request)
    refresh_token = d.get('refresh', '').strip()
    if not refresh_token:
        return JsonResponse(
            {'detail': "Refresh token kiritish shart."},
            status=400,
        )
    try:
        RefreshToken(refresh_token).blacklist()
    except TokenError:
        return JsonResponse(
            {'detail': "Token noto'g'ri yoki muddati o'tgan."},
            status=400,
        )
    return JsonResponse({'detail': "Tizimdan muvaffaqiyatli chiqdingiz."})


# ---------------------------------------------------------------------------
# Profile  — /api/v1/users/
# ---------------------------------------------------------------------------

@csrf_exempt
@jwt_required
@require_http_methods(['GET', 'PATCH'])
def profile(request):
    user = request.user

    if request.method == 'GET':
        return JsonResponse({'user': _user_payload(user)})

    # PATCH — supports both JSON body and multipart form
    if request.content_type and 'application/json' in request.content_type:
        data = _json(request)
    else:
        data = request.POST

    errors = {}
    dirty  = []

    for field in ('first_name', 'last_name'):
        if field in data:
            val = data[field].strip()
            if not val and field == 'first_name':
                errors['first_name'] = "Ism bo'sh bo'lishi mumkin emas."
                continue
            setattr(user, field, val)
            dirty.append(field)

    if 'grade' in data:
        if user.role != User.Role.STUDENT:
            errors['grade'] = "Sinf faqat o'quvchilar uchun."
        else:
            try:
                grade = int(data['grade'])
                if not (1 <= grade <= 11):
                    raise ValueError
                user.grade = grade
                dirty.append('grade')
            except (TypeError, ValueError):
                errors['grade'] = "Sinf 1–11 orasida butun son bo'lishi kerak."

    if errors:
        return JsonResponse({'errors': errors}, status=400)

    if 'avatar' in request.FILES:
        user.avatar = request.FILES['avatar']
        dirty.append('avatar')

    if dirty:
        user.save(update_fields=dirty)

    return JsonResponse({'user': _user_payload(user)})


# ---------------------------------------------------------------------------
# Parent–child  — /api/v1/users/
# ---------------------------------------------------------------------------

@csrf_exempt
@jwt_required
@require_http_methods(['GET', 'POST'])
def children(request):
    if request.user.role != User.Role.PARENT:
        return JsonResponse(
            {'detail': "Bu amal faqat ota-onalar uchun."},
            status=403,
        )

    if request.method == 'GET':
        kids = request.user.children.all().order_by('first_name')
        return JsonResponse({'children': [_user_payload(c) for c in kids]})

    # POST — add child by phone
    d     = _json(request)
    phone = d.get('phone', '').strip()
    if not phone:
        return JsonResponse(
            {'detail': "Farzandning telefon raqamini kiriting."},
            status=400,
        )
    try:
        child = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return JsonResponse(
            {'detail': "Bu raqamli foydalanuvchi topilmadi."},
            status=404,
        )
    if child.role != User.Role.STUDENT:
        return JsonResponse(
            {'detail': "Faqat o'quvchilarni farzand sifatida qo'shish mumkin."},
            status=400,
        )
    if child.pk == request.user.pk:
        return JsonResponse(
            {'detail': "O'zingizni farzand sifatida qo'sha olmaysiz."},
            status=400,
        )
    if request.user.children.filter(pk=child.pk).exists():
        return JsonResponse(
            {'detail': "Bu farzand allaqachon ro'yxatingizda."},
            status=400,
        )
    request.user.children.add(child)
    return JsonResponse({'child': _user_payload(child)}, status=201)


@csrf_exempt
@jwt_required
@require_http_methods(['DELETE'])
def child_remove(request, pk):
    if request.user.role != User.Role.PARENT:
        return JsonResponse(
            {'detail': "Bu amal faqat ota-onalar uchun."},
            status=403,
        )
    try:
        child = request.user.children.get(pk=pk)
    except User.DoesNotExist:
        return JsonResponse({'detail': "Farzand topilmadi."}, status=404)

    request.user.children.remove(child)
    return JsonResponse({}, status=204)
