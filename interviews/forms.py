from django import forms
from .models import InterviewSession
from questions.models import Domain


class StartSessionForm(forms.ModelForm):
    class Meta:
        model = InterviewSession
        fields = ['domain', 'level']
        widgets = {
            'domain': forms.RadioSelect(),
            'level': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['domain'].queryset = Domain.objects.all()
        self.fields['domain'].empty_label = None
        self.fields['level'].choices = [
            ('easy', 'Easy — fundamentals and common questions'),
            ('medium', 'Medium — standard interview difficulty'),
            ('hard', 'Hard — senior-level depth'),
        ]


class AnswerForm(forms.Form):
    text_input = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': 'Type your answer here, or use the voice recorder above...',
            'class': 'form-control'
        }),
        required=False,
        label='Your Answer'
    )
    audio_file = forms.FileField(required=False, label='Audio Recording')