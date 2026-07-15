"""
apps/academics/views.py

Admin-only list+create views for the Academic Structure section, plus one
shared delete view. Every list page follows the same pattern: a form to add
a new record at the top, and a table of existing records below — so a
single helper (`_list_create_view`) drives all 9 pages instead of repeating
the same boilerplate nine times.

Model-level `clean()` validation (e.g. AcademicYear's end-after-start check,
Subject's pass<=full check, SubjectClassMapping's level-match check,
TeacherSubjectAssignment's section-belongs-to-class check) runs
automatically through ModelForm.is_valid(), since Django calls
instance.full_clean() — including custom clean() — as part of that.
"""

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from apps.core.decorators import role_required

from .models import (
    AcademicYear,
    Level,
    SchoolClass,
    Section,
    Faculty,
    Shift,
    Subject,
    SubjectClassMapping,
    TeacherSubjectAssignment,
)
from .forms import (
    AcademicYearForm,
    LevelForm,
    SchoolClassForm,
    SectionForm,
    FacultyForm,
    ShiftForm,
    SubjectForm,
    SubjectClassMappingForm,
    TeacherSubjectAssignmentForm,
)


# ---------------------------------------------------------------------------
# Shared list+create helper
# ---------------------------------------------------------------------------

def _list_create_view(request, *, model, form_class, template_name,
                       list_context_name, select_related=None, active_page):
    qs = model.objects.all()
    if select_related:
        qs = qs.select_related(*select_related)

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, f"'{obj}' created successfully.")
                return redirect(request.path)
            except Exception as exc:
                messages.error(request, f"Error saving: {exc}")
        else:
            messages.error(request, "Please fix the errors highlighted below.")
    else:
        form = form_class()

    context = {
        'form': form,
        list_context_name: qs,
        'active_page': active_page,
    }
    return render(request, template_name, context)


# ---------------------------------------------------------------------------
# 1. Academic Years
# ---------------------------------------------------------------------------

@role_required('admin')
def academic_year_list(request):
    return _list_create_view(
        request,
        model=AcademicYear,
        form_class=AcademicYearForm,
        template_name='academics/academic_year_list.html',
        list_context_name='academic_years',
        active_page='academic_years',
    )


# ---------------------------------------------------------------------------
# 2. Levels
# ---------------------------------------------------------------------------

@role_required('admin')
def level_list(request):
    return _list_create_view(
        request,
        model=Level,
        form_class=LevelForm,
        template_name='academics/level_list.html',
        list_context_name='levels',
        active_page='levels',
    )


# ---------------------------------------------------------------------------
# 3. Classes
# ---------------------------------------------------------------------------

@role_required('admin')
def class_list(request):
    return _list_create_view(
        request,
        model=SchoolClass,
        form_class=SchoolClassForm,
        template_name='academics/class_list.html',
        list_context_name='classes',
        select_related=('level',),
        active_page='classes',
    )


# ---------------------------------------------------------------------------
# 4. Sections
# ---------------------------------------------------------------------------

@role_required('admin')
def section_list(request):
    return _list_create_view(
        request,
        model=Section,
        form_class=SectionForm,
        template_name='academics/section_list.html',
        list_context_name='sections',
        select_related=('school_class', 'school_class__level'),
        active_page='sections',
    )


# ---------------------------------------------------------------------------
# 5. Faculties
# ---------------------------------------------------------------------------

@role_required('admin')
def faculty_list(request):
    return _list_create_view(
        request,
        model=Faculty,
        form_class=FacultyForm,
        template_name='academics/faculty_list.html',
        list_context_name='faculties',
        select_related=('level',),
        active_page='faculties',
    )


# ---------------------------------------------------------------------------
# 6. Shifts
# ---------------------------------------------------------------------------

@role_required('admin')
def shift_list(request):
    return _list_create_view(
        request,
        model=Shift,
        form_class=ShiftForm,
        template_name='academics/shift_list.html',
        list_context_name='shifts',
        active_page='shifts',
    )


# ---------------------------------------------------------------------------
# 7. Subjects
# ---------------------------------------------------------------------------

@role_required('admin')
def subject_list(request):
    return _list_create_view(
        request,
        model=Subject,
        form_class=SubjectForm,
        template_name='academics/subject_list.html',
        list_context_name='subjects',
        select_related=('level',),
        active_page='subjects',
    )


# ---------------------------------------------------------------------------
# 8. Subject-Class Mapping
# ---------------------------------------------------------------------------

@role_required('admin')
def subject_class_mapping_list(request):
    return _list_create_view(
        request,
        model=SubjectClassMapping,
        form_class=SubjectClassMappingForm,
        template_name='academics/subject_class_mapping_list.html',
        list_context_name='mappings',
        select_related=('academic_year', 'school_class', 'subject', 'school_class__level'),
        active_page='subject_class_mapping',
    )


# ---------------------------------------------------------------------------
# 9. Teacher Subject Assignment
# ---------------------------------------------------------------------------

@role_required('admin')
def teacher_subject_assignment_list(request):
    return _list_create_view(
        request,
        model=TeacherSubjectAssignment,
        form_class=TeacherSubjectAssignmentForm,
        template_name='academics/teacher_subject_assignment_list.html',
        list_context_name='assignments',
        select_related=('teacher', 'subject', 'school_class', 'section', 'academic_year',
                         'teacher__user'),
        active_page='teacher_subject_assignment',
    )


# ---------------------------------------------------------------------------
# Shared delete view (used by all 9 tables' row "Delete" buttons)
# ---------------------------------------------------------------------------

_DELETABLE_MODELS = {
    'academic-year': AcademicYear,
    'level': Level,
    'class': SchoolClass,
    'section': Section,
    'faculty': Faculty,
    'shift': Shift,
    'subject': Subject,
    'subject-class-mapping': SubjectClassMapping,
    'teacher-subject-assignment': TeacherSubjectAssignment,
}


@role_required('admin')
def academics_delete(request, slug, pk):
    """
    Generic delete endpoint for any Academic Structure record, e.g.:
        POST /academics/level/7/delete/
    `slug` must be one of the keys in _DELETABLE_MODELS (kept to a fixed
    whitelist so this can't be used to delete arbitrary models).
    """
    model = _DELETABLE_MODELS.get(slug)
    if model is None:
        messages.error(request, "Unknown item type.")
        return redirect('admin_dashboard')

    obj = get_object_or_404(model, pk=pk)

    if request.method == 'POST':
        label = str(obj)
        try:
            obj.delete()
            messages.success(request, f"Deleted '{label}'.")
        except Exception as exc:
            messages.error(
                request,
                f"Could not delete '{label}' — it's likely still referenced "
                f"elsewhere (e.g. a class still has sections). ({exc})"
            )

    next_url = request.META.get('HTTP_REFERER')
    return redirect(next_url or 'admin_dashboard')


@role_required('teacher', 'admin')
def marks_entry(request):
    from apps.academics.models import Assessment, MarksEntry
    from apps.students.models import Student
    # pyrefly: ignore [missing-import]
    from apps.academics.services import create_marks_entry_bulk

    assessments = Assessment.objects.select_related('subject', 'school_class', 'section', 'term').all()
    if request.user.role == 'teacher':
        try:
            teacher = request.user.teacher_profile
            assessments = assessments.filter(created_by=teacher)
        except Exception:
            assessments = assessments.none()

    selected_assessment = None
    students = []
    existing_entries = {}

    assessment_id = request.GET.get('assessment') or request.POST.get('assessment')
    if assessment_id:
        selected_assessment = get_object_or_404(Assessment, pk=assessment_id)
        student_qs = Student.objects.filter(
            school_class=selected_assessment.school_class,
            status='active'
        )
        if selected_assessment.section:
            student_qs = student_qs.filter(section=selected_assessment.section)
        students = student_qs.select_related('user').order_by('roll_no', 'user__first_name')

        entries = MarksEntry.objects.filter(assessment=selected_assessment)
        existing_entries = {entry.student_id: entry for entry in entries}

    if request.method == 'POST' and selected_assessment:
        try:
            marks_data = []
            for student in students:
                marks_val = request.POST.get(f'marks_{student.id}')
                remarks = request.POST.get(f'remarks_{student.id}', '')
                if marks_val is not None and marks_val.strip() != '':
                    marks_data.append({
                        'student_id': student.id,
                        'marks_obtained': float(marks_val),
                        'remarks': remarks
                    })
            
            create_marks_entry_bulk(selected_assessment.id, marks_data, request.user)
            messages.success(request, f"Marks saved successfully for assessment: {selected_assessment.name}")
            return redirect(f"{request.path}?assessment={selected_assessment.id}")
        except Exception as e:
            messages.error(request, f"Error saving marks: {e}")

    context = {
        'assessments': assessments,
        'selected_assessment': selected_assessment,
        'students': students,
        'existing_entries': existing_entries,
        'active_page': 'marks_entry'
    }
    return render(request, 'academics/marks_entry.html', context)


@role_required('admin')
def marks_verify(request):
    from apps.academics.models import MarksEntry
    # pyrefly: ignore [missing-import]
    from apps.academics.services import verify_marks_entry

    unverified_entries = MarksEntry.objects.filter(is_verified=False).select_related(
        'student', 'student__user', 'assessment', 'assessment__subject', 'assessment__term'
    ).order_by('-created_at')

    if request.method == 'POST':
        entry_ids = request.POST.getlist('entry_ids')
        if entry_ids:
            try:
                count = 0
                for entry_id in entry_ids:
                    verify_marks_entry(entry_id, request.user)
                    count += 1
                messages.success(request, f"Successfully verified {count} marks entries.")
            except Exception as e:
                messages.error(request, f"Error verifying marks: {e}")
        else:
            messages.warning(request, "No entries selected.")
        return redirect(request.path)

    context = {
        'unverified_entries': unverified_entries,
        'active_page': 'marks_verify'
    }
    return render(request, 'academics/marks_verify.html', context)