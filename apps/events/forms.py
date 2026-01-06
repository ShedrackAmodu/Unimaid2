from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'time', 'location', 'max_attendees', 'registration_deadline']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 10}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class EventRegistrationForm(forms.Form):
    event_id = forms.IntegerField(widget=forms.HiddenInput())
