from django.urls import include, path
from .views import translatelab, translators, supervisors, ajax

urlpatterns = [
    path('', translatelab.home, name='home'),
    path('profile/', translatelab.user_profile, name='user_profile'),
    path('profile/change_password/', translatelab.user_change_password, name='user_change_password'),
    path('profile/update/', translatelab.UpdateProfile.as_view(), name='user_update_profile'),
    path('languages/<int:pk>/style_guide/', translatelab.LanguageDetailsView.as_view(), name='language_style_guide'),

    path('translators/', include(([
        path('', translators.TaskListView.as_view(), name='task_list'),
        path('languages/', translators.TranslatorLanguagesView.as_view(), name='translator_languages'),
        path('task/<int:pk>/details/', translators.TranslationDetailsView.as_view(), name='translation_details'),
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
        path('clients/', supervisors.ClientListView.as_view(), name='client_list'),
        path('clients/add/', supervisors.ClientCreateView.as_view(), name='client_add'),
        path('clients/<int:pk>/', supervisors.ClientDetailsView.as_view(), name='client_details'),
        path('clients/<int:pk>/edit/', supervisors.ClientUpdateView.as_view(), name='client_update'),
        path('task/add/', supervisors.TaskCreateView.as_view(), name='task_add'),
        path('task/export/', supervisors.task_csv_export_multi, name='csv_export'),
        path('task/import/', supervisors.task_csv_import, name='task_csv_import'),
        path('task/import/register/', supervisors.task_csv_import_register, name='task_csv_import_register'),
        path('task/<int:pk>/', supervisors.TaskDetailsView.as_view(), name='task_details'),
        path('task/<int:pk>/edit/', supervisors.TaskUpdateView.as_view(), name='task_change'),
        path('task/<int:pk>/delete/', supervisors.TaskDeleteView.as_view(), name='task_delete'),
        path('task/<int:pk>/approve/', supervisors.task_approve, name='task_approve'),
        path('task/<int:pk>/export/', supervisors.task_csv_export_single, name='csv_export_single'),
        path('task/<int:pk>/translation/<int:language_pk>/add/', supervisors.translation_add, name='translation_add'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/', supervisors.TranslationDetailsView.as_view(), name='translation_details'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/edit/', supervisors.translation_change, name='translation_change'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/cancel/', supervisors.translation_cancel, name='translation_cancel'),
        path('task/<int:task_pk>/translation/<int:translation_pk>/delete/', supervisors.TranslationDeleteView.as_view(), name='translation_delete'),
    ], 'translatelab'), namespace='supervisors')),

    path('ajax/', include(([
        path('language_style_guide/', ajax.load_language_styleguide, name='ajax_language_style_guide'),
    ], 'translatelab'), namespace='ajax')),
]


