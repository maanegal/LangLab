from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from datetime import datetime, timezone

from ..decorators import translator_required
from ..forms import TranslatorLanguagesForm, TranslatorSignUpForm, TranslationForm, ValidationForm
from ..models import Task, Translator, Translation, User, Language


class TranslatorSignUpView(CreateView):
    model = User
    form_class = TranslatorSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'translator'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('translators:task_list')


@method_decorator([login_required, translator_required], name='dispatch')
class TranslatorLanguagesView(UpdateView):
    model = Translator
    form_class = TranslatorLanguagesForm
    template_name = 'translatelab/translators/languages_form.html'
    success_url = reverse_lazy('translators:task_list')

    def get_object(self):
        return self.request.user.translator

    def form_valid(self, form):
        messages.success(self.request, 'Languages updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, translator_required], name='dispatch')
class TaskListView(ListView):
    model = Translation
    ordering = ('name', )
    context_object_name = 'translations'
    template_name = 'translatelab/translators/task_list.html'

    def get_context_data(self, **kwargs):
        kwargs['drafts'] = 'translator'
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        translator = self.request.user.translator
        translator_languages = translator.languages.values_list('pk', flat=True)

        queryset_trans = Translation.objects.filter(language__in=translator_languages)\
            .filter(task__source_language__in=translator_languages).exclude(translator__isnull=False)
        queryset_valid = Translation.objects.filter(language__in=translator_languages)\
            .filter(task__source_language__in=translator_languages)\
            .exclude(translator__isnull=True)\
            .exclude(translation_time_finished__isnull=True)\
            .exclude(validator__isnull=False)\
            .exclude(translator=translator)
        queryset = queryset_trans | queryset_valid
        return queryset


@method_decorator([login_required, translator_required], name='dispatch')
class DraftTaskListView(ListView):
    model = Translation
    context_object_name = 'translations'
    template_name = 'translatelab/translators/draft_task_list.html'

    def get_queryset(self):
        queryset_tran = self.request.user.translator.translations.filter(translation_time_finished__isnull=True) \
            .select_related('task') \
            .order_by('task__name')
        for t in queryset_tran:
            t.tasktype = 'Translation'
        queryset_val = self.request.user.translator.validated_translations.filter(translation_time_finished__isnull=True)\
            .select_related('task') \
            .order_by('task__name')
        for v in queryset_val:
            v.tasktype = 'Validation'
        queryset = queryset_tran | queryset_val
        return queryset


@method_decorator([login_required, translator_required], name='dispatch')
class DoneTaskListView(ListView):
    model = Translation
    context_object_name = 'translations'
    template_name = 'translatelab/translators/done_task_list.html'

    def get_queryset(self):
        queryset_tran = self.request.user.translator.translations.filter(translation_time_finished__isnull=False) \
            .select_related('task') \
            .order_by('task__name')
        for t in queryset_tran:
            t.tasktype = 'Translation'
        queryset_val = self.request.user.translator.validated_translations.filter(validation_time_finished__isnull=False) \
            .select_related('task') \
            .order_by('task__name')
        for v in queryset_val:
            v.tasktype = 'Validation'
        queryset = queryset_tran | queryset_val
        return queryset


@method_decorator([login_required, translator_required], name='dispatch')
class TranslationDetailsView(DetailView):
    model = Translation
    context_object_name = 'translation'
    template_name = 'translatelab/translators/translation_details.html'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        user = self.request.user
        translation = self.get_object()

        translation_started = bool(translation.translation_time_started)
        translation_finished = bool(translation.translation_time_finished)
        if translation.translator and translation.translator.user == user:
            translation_current_user = True
        else:
            translation_current_user = False
        validation_started = bool(translation.validation_time_started)
        validation_finished = bool(translation.validation_time_finished)
        if translation.validator and translation.validator.user == user:
            validation_current_user = True
        else:
            validation_current_user = False

        states = {1: 'Available', 2: 'Already assigned', 3: 'Draft', 4: 'Completed'}
        current_state = ''

        if not translation_started:
            current_state = states[1]
        elif translation_started and not translation_current_user and not translation_finished:
            current_state = states[2]
        elif translation_started and translation_current_user and not translation_finished:
            current_state = states[3]
        elif translation_started and translation_current_user and translation_finished:
            current_state = states[4]
        elif not validation_started and not translation_current_user and not validation_finished:
            current_state = states[1]
        elif not validation_started and translation_current_user:
            current_state = states[4]
        elif validation_started and not validation_current_user:
            current_state = states[2]
        elif validation_started and validation_current_user and not validation_finished:
            current_state = states[3]
        elif validation_started and validation_current_user and validation_finished:
            current_state = states[4]
        else:
            current_state = 'Error!'

        kwargs['current_state'] = current_state
        return super().get_context_data(**kwargs)


@login_required
@translator_required
def translate_task(request, pk):
    translation = get_object_or_404(Translation, pk=pk)
    translator = request.user.translator

    # If another translator has accepted the task already, redirect back to list
    if translation.translator and translation.translator != translator:
        messages.error(request, 'This task has already been accepted by another translator.')
        return redirect('translators:task_list')

    # Now, the translator has accepted the task. Register the information
    if not translation.translator:
        translation.translator = translator
        translation.translation_time_started = datetime.now(timezone.utc)
        translation.save()

    if request.method == 'POST':
        form = TranslationForm(request.POST, instance=translation)
        if form.is_valid():
            with transaction.atomic():
                finished_translation = form.save(commit=False)
                if 'finish' in request.POST:
                    finished_translation.translation_time_finished = datetime.now(timezone.utc)
                    messages.success(request, 'Translation was marked as finished. It will now be validated.')
                elif 'draft' in request.POST:
                    messages.success(request, 'Translation was saved as draft and can be resumed later.')
                finished_translation.save()
                form.save_m2m()
            return redirect('translators:task_list')

    else:
        form = TranslationForm(instance=translation)

    return render(request, 'translatelab/translators/do_translation_form.html', {
        'translation': translation,
        'form': form,
    })


@login_required
@translator_required
def validate_task(request, pk):
    translation = get_object_or_404(Translation, pk=pk)
    validator = request.user.translator

    # Make sure the validator and translator are not the same
    if translation.translator and translation.translator == validator:
        messages.error(request, 'This task has already been accepted by another translator.')
        return redirect('translators:task_list')

    # Now, the translator has accepted the task. Register the information
    if not translation.validator:
        translation.validator = validator
        translation.validation_time_started = datetime.now(timezone.utc)
        translation.save()

    if request.method == 'POST':
        form = ValidationForm(request.POST, instance=translation, initial={'validated_text': translation.text})
        if form.is_valid():
            with transaction.atomic():
                finished_validation = form.save(commit=False)
                if 'finish' in request.POST:
                    finished_validation.validation_time_finished = datetime.now(timezone.utc)
                    messages.success(request, 'Validation was marked as finished. It will be sent to a supervisor for final approval.')
                    if finished_validation.validated_text == finished_validation.text:
                        finished_validation.validated_text = ""
                elif 'draft' in request.POST:
                    messages.success(request, 'Validation was saved as draft and can be resumed later.')
                finished_validation.save()
                form.save_m2m()
            return redirect('translators:task_list')

    else:
        form = ValidationForm(instance=translation, initial={'validated_text': translation.text})

    return render(request, 'translatelab/translators/do_validation_form.html', {
        'translation': translation,
        'form': form,
    })


@login_required
@translator_required
def translation_cancel(request, pk):
    translation = get_object_or_404(Translation, pk=pk)
    user = request.user

    if translation.translator_id == user.id and not translation.translation_time_finished:
        translation.translator = None
        translation.translation_time_started = None
        translation.save()
    elif translation.validator_id == user.id and not translation.validation_time_finished:
        translation.validator = None
        translation.validation_time_started = None
        translation.save()

    return redirect('translators:task_list')
