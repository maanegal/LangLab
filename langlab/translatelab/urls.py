from django.urls import include, path

from .views import translatelab, translators, supervisors

urlpatterns = [
    path('', translatelab.home, name='home'),

    path('translators/', include(([
        path('', translators.TaskListView.as_view(), name='quiz_list'),
        path('languages/', translators.TranslatorLanguagesView.as_view(), name='translator_languages'),
        path('taken/', translators.PerformedTranslationsListView.as_view(), name='taken_quiz_list'),
        path('quiz/translation/<int:pk>/', translators.translate_task, name='translate_task'),
    ], 'translatelab'), namespace='translators')),

    path('supervisors/', include(([
        path('', supervisors.TaskListView.as_view(), name='quiz_change_list'),
        path('quiz/add/', supervisors.TaskCreateView.as_view(), name='quiz_add'),
        path('quiz/<int:pk>/', supervisors.TaskUpdateView.as_view(), name='quiz_change'),
        path('quiz/<int:pk>/delete/', supervisors.TaskDeleteView.as_view(), name='quiz_delete'),
        path('quiz/<int:pk>/results/', supervisors.QuizResultsView.as_view(), name='quiz_results'),
        path('quiz/<int:pk>/question/add/<int:language_pk>/', supervisors.question_add, name='question_add'),
        path('quiz/<int:quiz_pk>/question/<int:question_pk>/', supervisors.question_change, name='question_change'),
        path('quiz/<int:quiz_pk>/question/<int:question_pk>/delete/', supervisors.QuestionDeleteView.as_view(), name='question_delete'),
    ], 'translatelab'), namespace='supervisors')),
]
