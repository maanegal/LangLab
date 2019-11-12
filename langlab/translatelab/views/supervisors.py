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
                                  UpdateView)

from ..decorators import supervisor_required
from ..forms import TranslationForm, SupervisorSignUpForm, TaskCreateForm, TaskUpdateForm
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
        return redirect('supervisors:quiz_change_list')


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskListView(ListView):
    model = Task
    ordering = ('name', )
    context_object_name = 'tasks'
    template_name = 'translatelab/supervisors/quiz_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.tasks \
            .prefetch_related('target_languages') \
            .select_related('source_language')
        return queryset


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskCreateView(CreateView):
    model = Task
    form_class = TaskCreateForm
    template_name = 'translatelab/supervisors/quiz_add_form.html'

    def form_valid(self, form):
        task = form.save(commit=False)
        task.owner = self.request.user

        #task.time_created =
        # !! This is where processing will be done
        # for the objects selected in target_langs, create Translation (Question) objects
        task.save()
        for lang in form.cleaned_data['languages']:
            if not lang == task.source_language:  # filter out the source language
                t = task.questions.create(language=lang)
        form.save_m2m()  # save the many-to-many data for the form
        messages.success(self.request, 'The quiz was created with success! Go ahead and add some questions now.')
        return redirect('supervisors:quiz_change', task.pk)


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskUpdateForm
    context_object_name = 'quiz'
    template_name = 'translatelab/supervisors/quiz_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['other_target_languages'] = Language.objects\
            .exclude(translations__quiz__id=self.get_object().id)\
            .exclude(tasks_source__id=self.get_object().id)
        # this gets target languages not selected for this task
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        """
        This method is an implicit object-level permission management
        This view will only match the ids of existing tasks that belongs
        to the logged in user.
        """
        return self.request.user.tasks.all()

    def get_success_url(self):
        return reverse('supervisors:quiz_change', kwargs={'pk': self.object.pk})


@method_decorator([login_required, supervisor_required], name='dispatch')
class TaskDeleteView(DeleteView):
    model = Task
    context_object_name = 'quiz'
    template_name = 'translatelab/supervisors/quiz_delete_confirm.html'
    success_url = reverse_lazy('supervisors:quiz_change_list')

    def delete(self, request, *args, **kwargs):
        quiz = self.get_object()
        messages.success(request, 'The quiz %s was deleted with success!' % quiz.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.tasks.all()


@method_decorator([login_required, supervisor_required], name='dispatch')
class QuizResultsView(DetailView):
    model = Task
    context_object_name = 'quiz'
    template_name = 'translatelab/supervisors/quiz_results.html'

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        # !! clean this up. It should be removed
        taken_tasks = quiz.taken_tasks.select_related('translator__user').order_by('-date')
        total_taken_tasks = taken_tasks.count()
        quiz_score = quiz.taken_tasks.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_tasks': taken_tasks,
            'total_taken_tasks': total_taken_tasks,
            'quiz_score': quiz_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return self.request.user.tasks.all()


@login_required
@supervisor_required
def question_add(request, pk, language_pk):
    # By filtering the quiz by the url keyword argument `pk` and
    # by the owner, which is the logged in user, we are protecting
    # this view at the object-level. Meaning only the owner of
    # quiz will be able to add questions to it.
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    lang = Language.objects.get(pk=language_pk)

    translation = Translation(quiz=task, language=lang)
    translation.save()

    return redirect('supervisors:quiz_change', task.pk)


# Make a version of this for translators
@login_required
@supervisor_required
def question_change(request, quiz_pk, question_pk):
    # Simlar to the `question_add` view, this view is also managing
    # the permissions at object-level. By querying both `quiz` and
    # `question` we are making sure only the owner of the quiz can
    # change its details and also only questions that belongs to this
    # specific quiz can be changed via this url (in cases where the
    # user might have forged/player with the url params.
    quiz = get_object_or_404(Task, pk=quiz_pk, owner=request.user)
    question = get_object_or_404(Translation, pk=question_pk, quiz=quiz)

    if request.method == 'POST':
        form = TranslationForm(request.POST, instance=question)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, 'Translation saved with success!')
            return redirect('supervisors:quiz_change', quiz.pk)
    else:
        form = TranslationForm(instance=question)

    return render(request, 'translatelab/supervisors/question_change_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
    })


@method_decorator([login_required, supervisor_required], name='dispatch')
class QuestionDeleteView(DeleteView):
    model = Translation
    context_object_name = 'question'
    template_name = 'translatelab/supervisors/question_delete_confirm.html'
    pk_url_kwarg = 'question_pk'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        kwargs['quiz'] = question.quiz
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        question = self.get_object()
        messages.success(request, 'The question %s was deleted with success!' % question.text)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Translation.objects.filter(quiz__owner=self.request.user)

    def get_success_url(self):
        question = self.get_object()
        return reverse('supervisors:quiz_change', kwargs={'pk': question.quiz_id})
