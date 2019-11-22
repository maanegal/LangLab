from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from ..models import User, Language
from ..forms import UserUpdateForm


class SignUpView(TemplateView):
    template_name = 'registration/signup.html'


def home(request):
    if request.user.is_authenticated:
        if request.user.is_supervisor:
            return redirect('supervisors:task_change_list')
        else:
            return redirect('translators:task_list')
    return render(request, 'translatelab/home.html')


@method_decorator(login_required, name='dispatch')
class UserDetailsView(DetailView):
    model = User
    template_name = 'translatelab/supervisors/user_details.html'


@login_required
def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('home')

    return render(request, 'translatelab/user_profile.html')


@login_required
def user_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('user_profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'translatelab/user_change_password.html', {
        'form': form
    })


@method_decorator(login_required, name='dispatch')
class UpdateProfile(UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'translatelab/user_update_profile.html'
    success_url = reverse_lazy('user_profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class LanguageDetailsView(DetailView):
    model = Language
    template_name = 'translatelab/language_style_guide.html'
