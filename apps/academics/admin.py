"""
apps/academics/admin.py

Registers the Academic Structure models with Django admin so you can create
and inspect data immediately, before any custom views/templates exist.
"""

from django.contrib import admin

from .models import (
    AcademicYear, Level, SchoolClass, Section, Faculty, Shift,
    Subject, SubjectClassMapping, TeacherSubjectAssignment,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'status', 'is_current')
    list_filter = ('status', 'is_current')
    search_fields = ('name',)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'order', 'uses_faculty', 'uses_shift')
    ordering = ('order',)


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'order')
    list_filter = ('level',)
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_class', 'capacity')
    list_filter = ('school_class__level', 'school_class')


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'code')
    list_filter = ('level',)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'level', 'full_marks', 'pass_marks', 'is_elective', 'status')
    list_filter = ('level', 'is_elective', 'status')
    search_fields = ('name', 'code')


@admin.register(SubjectClassMapping)
class SubjectClassMappingAdmin(admin.ModelAdmin):
    list_display = ('subject', 'school_class', 'academic_year', 'is_compulsory')
    list_filter = ('academic_year', 'school_class__level', 'is_compulsory')


@admin.register(TeacherSubjectAssignment)
class TeacherSubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'school_class', 'section', 'academic_year')
    list_filter = ('academic_year', 'school_class__level', 'subject')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name')