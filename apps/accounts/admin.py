from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    # ── List view ────────────────────────────────────────────────────────────
    list_display = (
        'username', 'email', 'get_full_name',
        'role', 'is_active', 'is_staff', 'must_change_password', 'date_joined',
    )
    list_filter  = ('role', 'is_active', 'is_staff', 'must_change_password')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 25

    # ── Detail / edit view ────────────────────────────────────────────────────
    fieldsets = UserAdmin.fieldsets + (
        ('SmartSchool', {
            'fields': ('role', 'must_change_password', 'raw_password'),
        }),
    )

    # ── Create user in admin ──────────────────────────────────────────────────
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('SmartSchool', {
            'fields': ('email', 'role', 'must_change_password'),
        }),
    )

    readonly_fields = ('raw_password', 'date_joined', 'last_login')

    # ── Bulk actions ──────────────────────────────────────────────────────────
    actions = ['activate_users', 'deactivate_users', 'force_password_change']

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated.")

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated.")

    @admin.action(description='Force password change on next login')
    def force_password_change(self, request, queryset):
        updated = queryset.update(must_change_password=True)
        self.message_user(request, f"{updated} user(s) will be prompted to change password.")
