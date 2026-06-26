from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    # fields shown in admin list page
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')

    # filters on right side
    list_filter = ('role', 'is_staff', 'is_active')

    # fields when editing user
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'must_change_password')
        }),
    )

    # fields when creating user in admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'must_change_password')
        }),
    )

    search_fields = ('username', 'email')
    ordering = ('username',)