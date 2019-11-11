from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError

from .models import (Answer, Translation, Translator, TranslatorAnswer, Language, User, Task)


class SupervisorSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_supervisor = True
        if commit:
            user.save()
        return user


class TranslatorSignUpForm(UserCreationForm):
    languages = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_translator = True
        user.save()
        translator = Translator.objects.create(user=user)
        translator.languages.add(*self.cleaned_data.get('languages'))
        return user


class TranslatorLanguagesForm(forms.ModelForm):
    class Meta:
        model = Translator
        fields = ('languages', )
        widgets = {
            'languages': forms.CheckboxSelectMultiple
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = ('text', )


class BaseAnswerInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        has_one_correct_answer = False
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_correct', False):
                    has_one_correct_answer = True
                    break
        if not has_one_correct_answer:
            raise ValidationError('Mark at least one answer as correct.', code='no_correct_answer')


class TakeQuizForm(forms.ModelForm):
    answer = forms.ModelChoiceField(
        queryset=Answer.objects.none(),
        widget=forms.RadioSelect(),
        required=True,
        empty_label=None)

    class Meta:
        model = TranslatorAnswer
        fields = ('answer', )

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        super().__init__(*args, **kwargs)
        self.fields['answer'].queryset = question.answers.order_by('text')


class TaskCreateForm(forms.ModelForm):  # !! make a separate for update, with fewer fields
    languages = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Target languages. Selected source language will automatically be filtered out.")

    class Meta:
        model = Task
        fields = ('name', 'source_content', 'source_language', )


class TaskUpdateForm(forms.ModelForm):  # !! make a separate for update, with fewer fields
    class Meta:
        model = Task
        fields = ('name', 'source_content', 'source_language', )
