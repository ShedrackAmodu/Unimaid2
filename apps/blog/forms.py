# blog/forms.py
from django import forms
from .models import BlogPost
from django.utils import timezone

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'status', 'published_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title',
                'maxlength': '500'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your blog post content here...',
                'rows': 15
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'published_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make published_date optional
        self.fields['published_date'].required = False
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 10:
            raise forms.ValidationError("Title must be at least 10 characters long.")
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 50:
            raise forms.ValidationError("Content must be at least 50 characters long.")
        return content
    
    def clean_published_date(self):
        published_date = self.cleaned_data.get('published_date')
        status = self.cleaned_data.get('status')
        
        # If status is published but no published_date is set, set it to now
        if status == 'published' and not published_date:
            return timezone.now()
        
        return published_date