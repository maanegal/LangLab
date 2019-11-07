from django.urls import include, path

from .views import translatelab, translators, supervisors

urlpatterns = [
    path('', translatelab.home, name='home'),

    path('translators/', include(([
        path('', translators.QuizListView.as_view(), name='quiz_list'),
        path('interests/', translators.TranslatorInterestsView.as_view(), name='translator_interests'),
        path('taken/', translators.TakenQuizListView.as_view(), name='taken_quiz_list'),
        path('quiz/<int:pk>/', translators.take_quiz, name='take_quiz'),
    ], 'translatelab'), namespace='translators')),

    path('supervisors/', include(([
        path('', supervisors.QuizListView.as_view(), name='quiz_change_list'),
        path('quiz/add/', supervisors.QuizCreateView.as_view(), name='quiz_add'),
        path('quiz/<int:pk>/', supervisors.QuizUpdateView.as_view(), name='quiz_change'),
        path('quiz/<int:pk>/delete/', supervisors.QuizDeleteView.as_view(), name='quiz_delete'),
        path('quiz/<int:pk>/results/', supervisors.QuizResultsView.as_view(), name='quiz_results'),
        path('quiz/<int:pk>/question/add/', supervisors.question_add, name='question_add'),
        path('quiz/<int:quiz_pk>/question/<int:question_pk>/', supervisors.question_change, name='question_change'),
        path('quiz/<int:quiz_pk>/question/<int:question_pk>/delete/', supervisors.QuestionDeleteView.as_view(), name='question_delete'),
    ], 'translatelab'), namespace='supervisors')),
]
