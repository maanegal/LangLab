from django.urls import include, path
from django.contrib import admin

from translatelab.views import translatelab, translators, supervisors

urlpatterns = [
    path('', include('translatelab.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', translatelab.SignUpView.as_view(), name='signup'),
    path('accounts/signup/translator/', translators.TranslatorSignUpView.as_view(), name='translator_signup'),
    path('accounts/signup/supervisor/', supervisors.SupervisorSignUpView.as_view(), name='supervisor_signup'),
    path('admin/', admin.site.urls),
]
