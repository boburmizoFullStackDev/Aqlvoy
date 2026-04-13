from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('-date_joined',)
    list_display = ('phone', 'first_name', 'last_name', 'role', 'grade', 'total_points', 'is_active')
    list_filter = ('role', 'grade', 'is_active', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'avatar')}),
        (_('Role & learning'), {'fields': ('role', 'grade', 'total_points', 'children')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Dates'), {'fields': ('date_joined',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'first_name', 'last_name', 'role', 'grade', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('date_joined', 'total_points')
    filter_horizontal = ('children', 'groups', 'user_permissions')
