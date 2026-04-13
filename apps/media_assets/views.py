from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.users.decorators import jwt_required


@csrf_exempt
@jwt_required
@require_GET
def asset_list(request):
    # Returns all media assets (optionally filter by ?type=video etc.)
    # Business logic to be implemented
    return JsonResponse({}, status=501)


@csrf_exempt
@jwt_required
@require_POST
def asset_upload(request):
    file       = request.FILES.get('file')
    asset_type = request.POST.get('asset_type')
    if not file or not asset_type:
        return JsonResponse(
            {'error': 'file and asset_type are required.'},
            status=400,
        )
    # Business logic to be implemented
    return JsonResponse({}, status=501)


@csrf_exempt
@jwt_required
@require_http_methods(['GET', 'DELETE'])
def asset_detail(request, pk):
    # GET  — single asset detail
    # DELETE — remove asset (owner or admin only)
    # Business logic to be implemented
    return JsonResponse({}, status=501)
