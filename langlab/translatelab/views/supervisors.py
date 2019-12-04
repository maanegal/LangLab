from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView, UpdateView)
from django.http import HttpResponseRedirect
from django.db.models.functions import Lower
from io import TextIOWrapper

from ..decorators import supervisor_required
from ..forms import TranslationForm, SupervisorSignUpForm, TaskCreateForm, TaskUpdateForm, LanguageEditForm, \
    TaskSelectForm
from ..models import Translation, Task, User, Language, get_sentinel_user
from ..point_score import PointScore
from ..csv_data import csv_export, csv_import


class SupervisorSignUpView(CreateView):
    model = User
    form_class = SupervisorSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'supervisor'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('supervisors:task_change_list')


@method_decorator([login_required, supervisor_required], name='dispatch')
class UserListView(ListView):
    model = User
    context_object_name = 'users'
    template_name = 'translatelab/supervisors/user_list.html'

    def get_queryset(self):
        dummy = get_sentinel_user()  # this is a dirty hack, just to make sure that the "deleted user" is present, in case a user tries to sign up with that name
        queryset = User.objects.all()\
            .exclude(is_deleted=True)\
            .select_related('translator').order_by(Lower('username'))
        return queryset


@method_decorator([login_required, supervisor_required], name='dispatch')
class UserDetailsView(DetailView):
    model = User
    template_name = 'translatelab/supervisors/user_details.html'


@method_decorator([login_required, supervisor_required], name='dispatch')
class UserDeleteView(DeleteView):
    model = Language
    template_name = 'translatelab/supervisors/user_delete_confirm.html'
    context_object_name = 'task'
    success_url = reverse_lazy('supervisors:user_list')

    def delete(self, request, *args, **kwargs):
        user = self.get_object()

        sentinel = get_sentinel_user()
        transen = sentinel.translator
        ex_trans = user.translator.translations
        for t in ex_trans.all():
            t.translator = transen
            t.save()
        ex_validations = user.translator.validated_translations
        for t in ex_validations.all():
            t.validator = transen
            t.save()
        messages.success(request, 'The user %s was deleted with success!' % user.username)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.all()


@login_required
@supervisor_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)

    if user.is_translator:
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()

    return redirect('supervisors:user_details', user.pk)


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskListView(ListView):
    model = Task
    ordering = ('name', )
    context_object_name = 'tasks'
    template_name = 'translatelab/supervisors/task_change_list.html'

    def get_queryset(self):
        queryset = Task.objects.all().select_related('source_language', 'owner').prefetch_related('translations')
        return queryset

    def tasks_active(self):
        qs = super().get_queryset()
        active = qs.filter(status__lt=100, approved=False).order_by('-time_created')
        return active

    def tasks_awaiting(self):
        qs = super().get_queryset()
        awaiting = qs.filter(status=100, approved=False)
        return awaiting

    def tasks_completed(self):
        qs = super().get_queryset()
        completed = qs.filter(approved=True)
        return completed


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskCreateView(CreateView):
    model = Task
    form_class = TaskCreateForm
    template_name = 'translatelab/supervisors/task_add_form.html'

    def form_valid(self, form):
        task = form.save(commit=False)
        task.owner = self.request.user
        ps = PointScore(text=form.cleaned_data['source_content'], priority=form.cleaned_data['priority'])
        task.word_count = ps.word_count
        task.point_score = ps.score()
        task.point_score_version = ps.version
        task.save()
        for lang in form.cleaned_data['languages']:
            if not lang == task.source_language:  # filter out the source language
                t = task.translations.create(language=lang)
        form.save_m2m()  # save the many-to-many data for the form
        messages.success(self.request, 'The task was created')
        return redirect('supervisors:task_details', task.pk)


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskUpdateForm
    context_object_name = 'task'
    template_name = 'translatelab/supervisors/task_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['other_target_languages'] = Language.objects\
            .exclude(translations__task__id=self.get_object().id)\
            .exclude(tasks_source__id=self.get_object().id)
        # this gets target languages not selected for this task
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return Task.objects.all()

    def form_valid(self, form):
        task = form.save(commit=False)
        ps = PointScore(text=form.cleaned_data['source_content'], priority=form.cleaned_data['priority'])
        task.word_count = ps.word_count
        task.point_score = ps.score()
        task.point_score_version = ps.version
        task.save()
        form.save_m2m()  # save the many-to-many data for the form
        messages.success(self.request, 'The task was updated')
        return redirect('supervisors:task_details', task.pk)

    def get_success_url(self):
        return reverse('supervisors:task_details', kwargs={'pk': self.object.pk})


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskDeleteView(DeleteView):
    model = Task
    context_object_name = 'task'
    template_name = 'translatelab/supervisors/task_delete_confirm.html'
    success_url = reverse_lazy('supervisors:task_change_list')

    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        messages.success(request, 'The task %s was deleted with success!' % task.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Task.objects.all()


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskDetailsView(DetailView):
    model = Task
    template_name = 'translatelab/supervisors/task_details.html'


@login_required
@supervisor_required
def task_approve(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.get_status() == 100:
        points = task.point_score
        for translation in task.translations.all():
            translator = translation.translator
            validator = translation.validator
            translator.points_earned += points
            validator.points_earned += points
            translator.save()
            validator.save()
        task.approved = True
        task.save()
    return redirect('supervisors:task_details', task.pk)


@login_required
@supervisor_required
def translation_add(request, pk, language_pk):
    # By filtering the task by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # task will be able to add translations to it.
    task = get_object_or_404(Task, pk=pk)
    lang = Language.objects.get(pk=language_pk)

    translation = Translation(task=task, language=lang)
    translation.save()

    return redirect('supervisors:task_change', task.pk)


# Make a version of this for translators
@login_required
@supervisor_required
def translation_change(request, task_pk, translation_pk):
    # Simlar to the `translation_add` view, this view is also managing
    # the permissions at object-level. By querying both `task` and
    # `translation` we are making sure only the owner of the task can
    # change its details and also only translations that belongs to this
    # specific task can be changed via this url (in cases where the
    # user might have forged/player with the url params.
    task = get_object_or_404(Task, pk=task_pk)
    translation = get_object_or_404(Translation, pk=translation_pk, task=task)

    if request.method == 'POST':
        form = TranslationForm(request.POST, instance=translation)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, 'Translation saved with success!')
            return redirect('supervisors:task_change', task.pk)
    else:
        form = TranslationForm(instance=translation)

    return render(request, 'translatelab/supervisors/translation_change_form.html', {
        'task': task,
        'translation': translation,
        'form': form,
    })


@login_required
@supervisor_required
def translation_cancel(request, task_pk, translation_pk):
    translation = get_object_or_404(Translation, pk=translation_pk)

    if translation.translator and not translation.translation_time_finished:
        translation.translator = None
        translation.translation_time_started = None
        translation.save()
    elif translation.validator and not translation.validation_time_finished:
        translation.validator = None
        translation.validation_time_started = None
        translation.save()

    return redirect('supervisors:task_details', task_pk)


@method_decorator([login_required, supervisor_required], name='dispatch')
class TranslationDetailsView(DetailView):
    model = Translation
    template_name = 'translatelab/supervisors/translation_details.html'
    pk_url_kwarg = 'translation_pk'


@method_decorator([login_required, supervisor_required], name='dispatch')
class TranslationDeleteView(DeleteView):
    model = Translation
    context_object_name = 'translation'
    template_name = 'translatelab/supervisors/translation_delete_confirm.html'
    pk_url_kwarg = 'translation_pk'

    def get_context_data(self, **kwargs):
        translation = self.get_object()
        kwargs['task'] = translation.task
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        translation = self.get_object()
        messages.success(request, 'The translation into %s was deleted' % translation.language.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Translation.objects.filter(task__owner=self.request.user)

    def get_success_url(self):
        translation = self.get_object()
        return reverse('supervisors:task_change', kwargs={'pk': translation.task_id})


@method_decorator([login_required, supervisor_required], name='dispatch')
class LanguageEditView(CreateView):
    model = Language
    form_class = LanguageEditForm
    context_object_name = 'languages'
    template_name = 'translatelab/supervisors/language_edit_form.html'

    def get_context_data(self, **kwargs):
        kwargs['languages'] = Language.objects.all().exclude(name='Unknown')
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('supervisors:languages_edit')


@method_decorator([login_required, supervisor_required], name='dispatch')
class LanguageUpdateView(UpdateView):
    model = Language
    form_class = LanguageEditForm
    context_object_name = 'languages'
    template_name = 'translatelab/supervisors/language_update_form.html'

    def get_success_url(self):
        return reverse('supervisors:languages_edit')


@method_decorator([login_required, supervisor_required], name='dispatch')
class LanguageDeleteView(DeleteView):
    model = Language
    template_name = 'translatelab/supervisors/language_delete_confirm.html'
    success_url = reverse_lazy('supervisors:languages_edit')


@login_required
@supervisor_required
def task_csv_export_multi(request):
    tasks = Task.objects.all()
    if request.method == 'POST':
        list_of_ids = request.POST.getlist('task_list')
        task_list = Task.objects.filter(id__in=list_of_ids)
        response = csv_export(task_list)
        return response

    return render(request, 'translatelab/supervisors/task_csv_export.html', {
        'tasks': tasks
    })


@login_required
@supervisor_required
def task_csv_export_single(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    response = csv_export([task])
    return response


@login_required
@supervisor_required
def task_csv_import(request):
    if request.method == 'POST':
        csv_file = request.FILES["csv_file"]
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File is not CSV type')
            return HttpResponseRedirect(reverse("supervisors:task_csv_import"))
        # if file is too large, return
        if csv_file.multiple_chunks():
            messages.error(request, "Uploaded file is too big (%.2f MB)." % (csv_file.size / (1000 * 1000),))
            return HttpResponseRedirect(reverse("supervisors:task_csv_import"))
        # perform csv import routine
        csv_input = csv_import(csv_file)
        request.session['csv_input'] = csv_input
        return redirect('supervisors:task_csv_import_register')
    else:
        return render(request, 'translatelab/supervisors/task_csv_import.html')


@login_required
@supervisor_required
def task_csv_import_register(request):
    csv_input = request.session['csv_input']
    if not csv_input:
        messages.error(request, 'Could not process data')
        return HttpResponseRedirect(reverse("supervisors:task_csv_import"))

    tasks = []
    num = 1
    for c in csv_input:
        task = Task(name=c['name'], source_content=c['text'], instructions=c['instructions'], priority=c['priority'])
        if c.get('source_language', None):
            task.source_language = Language.objects.get(id=c.get('source_language'))
        langs = Language.objects.filter(id__in=c['target_languages']).exclude(name="Unknown")
        form = TaskCreateForm(instance=task, initial={'languages': langs}, prefix='task'+str(num))
        d = {'task': task, 'form': form, 'raw_data': str(c), 'num': num}
        tasks.append(d)
        num += 1

    if request.method == 'POST':
        for task in tasks:
            form = TaskCreateForm(request.POST, instance=task['task'], prefix='task'+str(task['num']))
            print(form)
            if form.is_valid():
                task = form.save(commit=False)
                task.owner = request.user
                ps = PointScore(text=form.cleaned_data['source_content'], priority=form.cleaned_data['priority'])
                task.word_count = ps.word_count
                task.point_score = ps.score()
                task.point_score_version = ps.version
                task.save()
                for lang in form.cleaned_data['languages']:
                    if not lang == task.source_language:  # filter out the source language
                        t = task.translations.create(language=lang)
                form.save_m2m()  # save the many-to-many data for the form
        messages.success(request, 'Tasks added')
        return redirect('supervisors:task_change_list')

    return render(request, 'translatelab/supervisors/task_csv_import_register.html', {'tasks': tasks})
