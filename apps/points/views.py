from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from apps.users.decorators import jwt_required


@csrf_exempt
@jwt_required
@require_GET
def point_history(request):
    # Returns the authenticated user's PointTransaction list
    # Business logic to be implemented
    return JsonResponse({}, status=501)


@csrf_exempt
@jwt_required
@require_GET
def leaderboard(request):
    # Returns top-N users sorted by total_points
    # Business logic to be implemented
    return JsonResponse({}, status=501)
