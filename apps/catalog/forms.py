from django import forms
from django.forms import ModelForm, Select
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Author, Publisher, Faculty, Department, Topic, Genre, Book, BookCopy


class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['name', 'description', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'code', 'faculty']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-control'}),
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'description', 'code', 'department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter departments by faculty if faculty is selected
        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['department'].queryset = Department.objects.filter(faculty_id=faculty_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.department:
            self.fields['department'].queryset = Department.objects.filter(faculty=self.instance.department.faculty)


class BookForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(
        queryset=Author.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        help_text="Hold Ctrl (Cmd on Mac) to select multiple authors"
    )

    class Meta:
        model = Book
        fields = ['title', 'isbn', 'authors', 'publisher', 'faculty', 'department', 'topic', 'genre',
                 'description', 'publication_date', 'edition', 'pages', 'language']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'publisher': forms.Select(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'topic': forms.Select(attrs={'class': 'form-control'}),
            'genre': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'publication_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'edition': forms.TextInput(attrs={'class': 'form-control'}),
            'pages': forms.NumberInput(attrs={'class': 'form-control'}),
            'language': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add help links for creating new entities
        faculty_help = mark_safe(
            'Select a faculty or <a href="#" onclick="window.open(\'/admin/catalog/faculty/add/\', \'_blank\', \'width=800,height=600\'); return false;" class="text-primary">create new faculty</a>'
        )
        department_help = mark_safe(
            'Select a department or <a href="#" onclick="window.open(\'/admin/catalog/department/add/\', \'_blank\', \'width=800,height=600\'); return false;" class="text-primary">create new department</a>'
        )
        topic_help = mark_safe(
            'Select a topic or <a href="#" onclick="window.open(\'/admin/catalog/topic/add/\', \'_blank\', \'width=800,height=600\'); return false;" class="text-primary">create new topic</a>'
        )

        self.fields['faculty'].help_text = faculty_help
        self.fields['department'].help_text = department_help
        self.fields['topic'].help_text = topic_help

        # Filter departments by faculty
        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['department'].queryset = Department.objects.filter(faculty_id=faculty_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.faculty:
            self.fields['department'].queryset = Department.objects.filter(faculty=self.instance.faculty)

        # Filter topics by department
        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['topic'].queryset = Topic.objects.filter(department_id=department_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.department:
            self.fields['topic'].queryset = Topic.objects.filter(department=self.instance.department)


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'bio']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class PublisherForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ['name', 'address', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BookCopyForm(forms.ModelForm):
    class Meta:
        model = BookCopy
        fields = ['book', 'barcode', 'condition', 'status', 'acquisition_date', 'location']
        widgets = {
            'book': forms.Select(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'acquisition_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }
