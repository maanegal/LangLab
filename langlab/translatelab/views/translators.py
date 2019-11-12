from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView
from datetime import datetime

from ..decorators import translator_required
from ..forms import TranslatorLanguagesForm, TranslatorSignUpForm, TranslationForm
from ..models import Task, Translator, Translation, User


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

    def get_queryset(self):
        translator = self.request.user.translator
        translator_languages = translator.languages.values_list('pk', flat=True)

        queryset = Translation.objects.filter(language__in=translator_languages) \
            .exclude(translator__isnull=False)
        return queryset


@method_decorator([login_required, translator_required], name='dispatch')
class PerformedTranslationsListView(ListView):
    model = Translation
    context_object_name = 'translations'
    template_name = 'translatelab/translators/taken_task_list.html'

    def get_queryset(self):
        queryset = self.request.user.translator.translations.filter(translation_time_finished__isnull=False) \
            .select_related('task') \
            .order_by('task__name')
        return queryset


@login_required
@translator_required
def translate_task(request, pk):
    translation = get_object_or_404(Translation, pk=pk)
    translator = request.user.translator

    # If this translator has performed this translation earlier
    if translator.translations.filter(pk=pk).exists():
        return render(request, 'translatelab/translators/taken_task_list.html')

    # If another translator has accepted the task already, redirect back to list
    if translation.translator and translation.translator.filter(pk__isnull=False):
        return redirect('translators:task_list')
        # !! note: give some error message/explanation here

    # Now, the translator has accepted the task. Register the information
    translation.translator = translator
    translation.translation_time_started = datetime.now()  # !! make sure that this is right. Maybe do something directly in DB
    translation.save()
    if request.method == 'POST':
        form = TranslationForm(request.POST, instance=translation)
        if form.is_valid():
            with transaction.atomic():
                finished_translation = form.save(commit=False)
                finished_translation.translation_time_finished = datetime.now()
                finished_translation.save()
                form.save_m2m()
            return redirect('translators:task_list')
            # !! give a notice to the translator

    else:
        form = TranslationForm(instance=translation)

    return render(request, 'translatelab/translators/take_task_form.html', {
        'translation': translation,
        'form': form,
    })
