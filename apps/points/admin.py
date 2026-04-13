from django.contrib import admin

from .models import PointTransaction


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'delta', 'source', 'balance_after', 'task_attempt', 'created_at')
    list_filter = ('source',)
    search_fields = ('user__phone', 'user__first_name', 'note')
    readonly_fields = ('user', 'delta', 'source', 'balance_after', 'task_attempt', 'created_at')

    def has_add_permission(self, request):
        return False  # Transactions are created programmatically only

    def has_delete_permission(self, request, obj=None):
        return False  # Ledger entries are immutable
