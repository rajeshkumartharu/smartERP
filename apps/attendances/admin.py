from django.contrib import admin

from .models import ClassTeacherAssignment, AttendanceSession, AttendanceRecord


@admin.register(ClassTeacherAssignment)
class ClassTeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'teacher', 'academic_year', 'school_class', 'section', 'is_active', 'assigned_at'
    )
    list_filter = ('academic_year', 'school_class', 'section', 'is_active')
    search_fields = (
        'teacher__user__first_name',
        'teacher__user__last_name',
        'school_class__name',
        'section__name',
    )


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = (
        'academic_year', 'school_class', 'section', 'date', 'marked_by',
        'present_count', 'absent_count', 'late_count', 'leave_count'
    )
    list_filter = ('academic_year', 'school_class', 'section', 'date')
    search_fields = ('school_class__name', 'section__name')
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('attendance_session', 'student', 'status', 'notified_parent')
    list_filter = ('status', 'notified_parent', 'attendance_session__date')
    search_fields = (
        'student__user__first_name',
        'student__user__last_name',
        'student__roll_no',
    )