from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ..models import Language


@login_required
def load_language_styleguide(request):
    lid = request.GET.get('style_guide', None)
    lang = Language.objects.filter(id__iexact=lid).first()
    if lang:
        sg = lang.style_guide
    else:
        sg = None
    data = {
        'style_guide': sg
    }
    return JsonResponse(data)
