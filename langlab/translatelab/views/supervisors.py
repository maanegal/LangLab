from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
#from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView, TemplateView)

from ..decorators import supervisor_required
from ..forms import TranslationForm, SupervisorSignUpForm, TaskCreateForm, TaskUpdateForm, LanguageEditForm
from ..models import Translation, Task, User, Language


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
class TaskListView(ListView):
    model = Task
    ordering = ('name', )
    context_object_name = 'tasks'
    template_name = 'translatelab/supervisors/task_change_list.html'

    def get_queryset(self):
        queryset = Task.objects.all() \
            .prefetch_related('target_languages') \
            .select_related('source_language')
        return queryset


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskCreateView(CreateView):
    model = Task
    form_class = TaskCreateForm
    template_name = 'translatelab/supervisors/task_add_form.html'

    def form_valid(self, form):
        task = form.save(commit=False)
        task.owner = self.request.user

        #task.time_created =
        # !! This is where processing will be done
        # for the objects selected in target_langs, create Translation objects
        task.save()
        for lang in form.cleaned_data['languages']:
            if not lang == task.source_language:  # filter out the source language
                t = task.translations.create(language=lang)
        form.save_m2m()  # save the many-to-many data for the form
        messages.success(self.request, 'The task was created with success! Go ahead and add some translations now.')
        return redirect('supervisors:task_change', task.pk)


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

    def get_success_url(self):
        return reverse('supervisors:task_change', kwargs={'pk': self.object.pk})


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
class TaskResultsView(DetailView):
    model = Task
    context_object_name = 'task'
    template_name = 'translatelab/supervisors/task_results.html'

    def get_context_data(self, **kwargs):
        task = self.get_object()
        # !! clean this up. It should be removed
        taken_tasks = task.taken_tasks.select_related('translator__user').order_by('-date')
        total_taken_tasks = taken_tasks.count()
        task_score = task.taken_tasks.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_tasks': taken_tasks,
            'total_taken_tasks': total_taken_tasks,
            'task_score': task_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return Task.objects.all()


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
    # !! add https://github.com/charettes/django-colorful
    model = Language
    form_class = LanguageEditForm
    context_object_name = 'languages'
    template_name = 'translatelab/supervisors/language_edit_form.html'

    def get_context_data(self, **kwargs):
        kwargs['languages'] = Language.objects.all()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('supervisors:languages_edit')


@method_decorator([login_required, supervisor_required], name='dispatch')
class LanguageDeleteView(DeleteView):
    model = Language
    template_name = 'translatelab/supervisors/language_delete_confirm.html'
    success_url = reverse_lazy('supervisors:languages_edit')
