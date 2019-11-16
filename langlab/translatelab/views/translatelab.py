from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from ..models import User


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
