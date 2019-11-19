from django.urls import include, path
from .views import translatelab, translators, supervisors

urlpatterns = [
    path('', translatelab.home, name='home'),
    path('profile/', translatelab.user_profile, name='user_profile'),
    path('profile/change_password/', translatelab.user_change_password, name='user_change_password'),
    path('profile/change_email/', translatelab.UpdateProfile.as_view(), name='user_change_email'),

    path('translators/', include(([
        path('', translators.TaskListView.as_view(), name='task_list'),
        path('languages/', translators.TranslatorLanguagesView.as_view(), name='translator_languages'),
        path('taken/', translators.DoneTaskListView.as_view(), name='taken_task_list'),
        path('task/translation/<int:pk>/', translators.translate_task, name='translate_task'),
        path('task/translation/<int:pk>/cancel', translators.translation_cancel, name='translation_cancel'),
        path('task/validation/<int:pk>/', translators.validate_task, name='validate_task'),
    ], 'translatelab'), namespace='translators')),

    path('supervisors/', include(([
        path('', supervisors.TaskListView.as_view(), name='task_change_list'),
        path('languages/', supervisors.LanguageEditView.as_view(), name='languages_edit'),
        path('languages/<int:pk>/delete/', supervisors.LanguageDeleteView.as_view(), name='language_delete'),
        path('languages/<int:pk>/update/', supervisors.LanguageUpdateView.as_view(), name='language_update'),
        path('users/', supervisors.UserListView.as_view(), name='user_list'),
        path('users/<int:pk>/', supervisors.UserDetailsView.as_view(), name='user_details'),
        path('users/<int:pk>/delete/', supervisors.UserDeleteView.as_view(), name='user_delete'),
        path('users/<int:pk>/toggle_active/', supervisors.user_toggle_active, name='user_toggle_active'),
        path('task/add/', supervisors.TaskCreateView.as_view(), name='task_add'),
        path('task/<int:pk>/', supervisors.TaskDetailsView.as_view(), name='task_details'),
        path('task/<int:pk>/update/', supervisors.TaskUpdateView.as_view(), name='task_change'),
        path('task/<int:pk>/delete/', supervisors.TaskDeleteView.as_view(), name='task_delete'),
        path('task/<int:pk>/approve/', supervisors.task_approve, name='task_approve'),
        path('task/<int:pk>/translation/add/<int:language_pk>/', supervisors.translation_add, name='translation_add'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/', supervisors.translation_change, name='translation_change'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/cancel/', supervisors.translation_cancel, name='translation_cancel'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/delete/', supervisors.TranslationDeleteView.as_view(), name='translation_delete'),
    ], 'translatelab'), namespace='supervisors')),
]


