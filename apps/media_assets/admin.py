from django.contrib import admin

from .models import MediaAsset


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('title', 'asset_type', 'subject', 'topic', 'uploaded_by', 'size_bytes', 'created_at')
    list_filter = ('asset_type', 'subject')
    search_fields = ('title',)
    readonly_fields = ('size_bytes', 'created_at', 'uploaded_by')

    fieldsets = (
        (None, {'fields': ('title', 'asset_type', 'thumbnail')}),
        ('File', {'fields': ('file', 'external_url', 'size_bytes')}),
        ('Curriculum link', {'fields': ('subject', 'topic')}),
        ('Meta', {'fields': ('uploaded_by', 'created_at')}),
    )
