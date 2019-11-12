from django.urls import include, path

from .views import translatelab, translators, supervisors

urlpatterns = [
    path('', translatelab.home, name='home'),

    path('translators/', include(([
        path('', translators.TaskListView.as_view(), name='task_list'),
        path('languages/', translators.TranslatorLanguagesView.as_view(), name='translator_languages'),
        path('taken/', translators.PerformedTranslationsListView.as_view(), name='taken_task_list'),
        path('task/translation/<int:pk>/', translators.translate_task, name='translate_task'),
    ], 'translatelab'), namespace='translators')),

    path('supervisors/', include(([
        path('', supervisors.TaskListView.as_view(), name='task_change_list'),
        path('task/add/', supervisors.TaskCreateView.as_view(), name='task_add'),
        path('task/<int:pk>/', supervisors.TaskUpdateView.as_view(), name='task_change'),
        path('task/<int:pk>/delete/', supervisors.TaskDeleteView.as_view(), name='task_delete'),
        path('task/<int:pk>/results/', supervisors.TaskResultsView.as_view(), name='task_results'),
        path('task/<int:pk>/translation/add/<int:language_pk>/', supervisors.translation_add, name='translation_add'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/', supervisors.translation_change, name='_change'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/delete/', supervisors.TranslationDeleteView.as_view(), name='translation_delete'),
    ], 'translatelab'), namespace='supervisors')),
]
