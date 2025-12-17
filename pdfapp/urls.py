from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import TemplateView
from . import views
from .views import register
from .utils.edit import download_pdf, open_editor, save_pdf
from django.http import HttpResponse

urlpatterns = [
    path('', views.register, name='register'),
    path('', views.register, name='register'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('navbar/', views.navbar, name='navbar'),
    path('logout/', views.logout, name='logout'),
    path('compress/', views.compress, name='compress'),
    path('convert/', views.convert, name='convert'),
    path('merge/', views.merge, name='merge'),
    path('edit/', views.edit_page, name='edit'),
    path('editor/<path:pdf_path>/', views.editor_page, name='editor_page'),
    path('open-editor/', open_editor, name='open_editor'),
    path('download/<str:pdf_path>/',download_pdf, name='download_pdf'),
    path('save-pdf/', save_pdf, name='save_pdf'),
    path('ai/', views.ai, name='ai'),
    path('summarization/', views.summarization_view, name='summarization'),
    path('translation/', views.translation_view, name='translation'),
    # path('health',health),
    
]

def health(request):
    return HttpResponse("OK", content_type="text/plain")

# Add media URL patterns in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
