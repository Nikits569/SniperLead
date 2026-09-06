from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.views.i18n import set_language
from django.http import HttpResponseRedirect
from django.utils.translation import check_for_language

def custom_set_language(request):
    response = set_language(request)
    if request.method == 'POST':
        lang_code = request.POST.get('language')
        if lang_code and check_for_language(lang_code):
            next_url = request.POST.get('next', '/')
            path_parts = next_url.lstrip('/').split('/')
            if path_parts and path_parts[0] in ['sk', 'uk', 'en']:
                path_parts[0] = lang_code
            else:
                path_parts.insert(0, lang_code)
            new_url = '/' + '/'.join(path_parts)
            return HttpResponseRedirect(new_url)
    return response

urlpatterns = [
    path("", RedirectView.as_view(url="/sk/", permanent=False)),
    path("i18n/setlang/", custom_set_language, name="set_language"),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path("", include("landing.urls")),
    path("", include("account.urls")),
    path('i18n/', include('django.conf.urls.i18n')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)