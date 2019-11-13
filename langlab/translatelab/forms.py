from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError

from .models import (Translation, Translator, Language, User, Task)


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


class TranslationForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = ('text', )


class ValidationForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = ('validated_text', )


class TaskCreateForm(forms.ModelForm):
    languages = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Target languages. Selected source language will automatically be filtered out.")

    class Meta:
        model = Task
        fields = ('name', 'source_content', 'priority', 'source_language', )


class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('name', 'source_content', 'priority', 'source_language', )


class LanguageEditForm(forms.ModelForm):
    class Meta:
        model = Language
        fields = ('name', 'color', )
