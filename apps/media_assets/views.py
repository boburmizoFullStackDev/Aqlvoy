from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.users.decorators import jwt_required

from .models import MediaAsset


def _asset_payload(asset):
    return {
        'id':         asset.id,
        'title':      asset.title,
        'asset_type': asset.asset_type,
        'url':        asset.external_url or (asset.file.url if asset.file else None),
        'thumbnail':  asset.thumbnail.url if asset.thumbnail else None,
        'subject_id': asset.subject_id,
        'topic_id':   asset.topic_id,
    }


@csrf_exempt
@jwt_required
@require_GET
def asset_list(request):
    """
    GET /api/v1/media-assets/
    Optional filters: ?grade=<1-11>  ?type=video|game|audio|image|document
    """
    qs = MediaAsset.objects.select_related('subject', 'topic__book').all()

    grade = request.GET.get('grade')
    if grade is not None:
        try:
            grade = int(grade)
        except ValueError:
            return JsonResponse({'error': 'grade must be an integer.'}, status=400)
        qs = qs.filter(
            Q(topic__book__grade=grade) | Q(subject__books__grade=grade)
        ).distinct()

    asset_type = request.GET.get('type')
    if asset_type:
        qs = qs.filter(asset_type=asset_type)

    return JsonResponse({'assets': [_asset_payload(a) for a in qs]})


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
