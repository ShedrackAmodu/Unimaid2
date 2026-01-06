from django import forms
from .models import Document


class DocumentForm(forms.ModelForm):
    authors = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Enter authors separated by commas"
    )

    class Meta:
        model = Document
        fields = ['title', 'authors', 'abstract', 'file', 'access_level', 'doi', 'collection']
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 5}),
        }
