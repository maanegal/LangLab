from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import EmailField
from django.db import transaction
from django.forms.utils import ValidationError


from .models import (Translation, Translator, Language, User, Task)


class SupervisorSignUpForm(UserCreationForm):
    email = EmailField(label="Email address", required=True, help_text="Required.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_supervisor = True
        if commit:
            user.save()
        return user


class TranslatorSignUpForm(UserCreationForm):
    languages = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all().exclude(name='Unknown'),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    email = EmailField(label="Email address", required=True, help_text="Required.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_translator = True
        user.email = self.cleaned_data["email"]
        user.save()
        translator = Translator.objects.create(user=user)
        translator.languages.add(*self.cleaned_data.get('languages'))
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'timezone',)


class TranslatorLanguagesForm(forms.ModelForm):
    class Meta:
        model = Translator
        fields = ('languages', )
        widgets = {
            'languages': forms.CheckboxSelectMultiple
        }

    def __init__(self, *args, **kwargs):
        super(TranslatorLanguagesForm, self).__init__(*args, **kwargs)
        self.fields['languages'].queryset = Language.objects.exclude(name='Unknown')


class TranslationForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = ('text', 'comment', )


class ValidationForm(forms.ModelForm):
    class Meta:
        model = Translation
        fields = ('validated_text', 'comment', )


class TaskCreateForm(forms.ModelForm):
    languages = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all().exclude(name='Unknown'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Target languages. Selected source language will automatically be filtered out.")

    class Meta:
        model = Task
        fields = ('name', 'source_content', 'priority', 'source_language', 'instructions', )

    def __init__(self, *args, **kwargs):
        super(TaskCreateForm, self).__init__(*args, **kwargs)
        self.fields['source_language'].queryset = Language.objects.exclude(name='Unknown')


class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('name', 'source_content', 'priority', 'source_language', )


class LanguageEditForm(forms.ModelForm):
    class Meta:
        model = Language
        fields = ('name', 'code', 'style_guide')


class TaskSelectForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('name', )
        widgets = {
            'name': forms.CheckboxSelectMultiple
        }
