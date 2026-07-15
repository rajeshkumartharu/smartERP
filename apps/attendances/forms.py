from django import forms
from django.utils import timezone

from .models import AttendanceSession


class AttendanceTakeForm(forms.Form):
    """
    Header form for teacher attendance page.
    Students/status rows are rendered manually in template and parsed in view.
    """
    date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
    )


class AttendanceHistoryFilterForm(forms.Form):
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    month = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Month'})
    )
    year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'})
    )


class AdminAttendanceFilterForm(forms.Form):
    academic_year = forms.IntegerField(required=False)
    school_class = forms.IntegerField(required=False)
    section = forms.IntegerField(required=False)
    date = forms.DateField(required=False)