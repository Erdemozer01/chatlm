from django import forms

from ask.models import Ask


class AskForm(forms.ModelForm):

    question = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Ask
        fields = ['question']
