from django.db import models
from django.conf import settings


def asset_upload_path(instance, filename):
    return f'assets/{instance.asset_type}/{filename}'


class MediaAsset(models.Model):
    class AssetType(models.TextChoices):
        VIDEO = 'video', 'Video'
        GAME = 'game', 'Game'
        AUDIO = 'audio', 'Audio'
        IMAGE = 'image', 'Image'
        DOCUMENT = 'document', 'Document'

    title = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=AssetType.choices)

    # Either an uploaded file or an external URL (e.g. YouTube embed, hosted game)
    file = models.FileField(upload_to=asset_upload_path, blank=True, null=True)
    external_url = models.URLField(
        blank=True,
        help_text='YouTube link, hosted game URL, etc. Use instead of file when applicable.',
    )
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)

    # Curriculum links — both optional so assets can be standalone
    subject = models.ForeignKey(
        'content.Subject', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='media_assets',
    )
    topic = models.ForeignKey(
        'content.Topic', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='media_assets',
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='uploaded_assets',
    )
    size_bytes = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Media Asset'
        verbose_name_plural = 'Media Assets'

    def __str__(self):
        return f'[{self.get_asset_type_display()}] {self.title}'
