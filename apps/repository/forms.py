from django import forms
from .models import EBook


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class EBookForm(forms.ModelForm):
    authors = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Enter authors separated by commas"
    )

    class Meta:
        model = EBook
        fields = ['title', 'authors', 'abstract', 'file', 'access_level', 'doi', 'collection']
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 5}),
        }


class BulkUploadForm(forms.Form):
    """Form for bulk uploading multiple eBook files."""
    files = forms.FileField(
        widget=MultipleFileInput(attrs={'multiple': True}),
        help_text="Select multiple eBook files to upload",
        label="eBook Files"
    )
    access_level = forms.ChoiceField(
        choices=EBook.ACCESS_LEVEL_CHOICES,
        initial='open',
        help_text="Access level for all uploaded eBooks"
    )
    collection = forms.ModelChoiceField(
        queryset=None,  # Will be set in view
        required=False,
        empty_label="No collection",
        help_text="Assign all eBooks to this collection (optional)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Collection
        self.fields['collection'].queryset = Collection.objects.all()
