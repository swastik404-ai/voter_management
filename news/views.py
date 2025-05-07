from PIL.features import features
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib import messages

from .models import News, ArchivedNews
from .serializers import NewsSerializer

# API: DRF ViewSet for News
class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        ArchivedNews.objects.create(news=instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Public form view (not admin)
class NewsFormView(View):
    def get(self, request):
        return render(request, 'news/news_form.html')

    def post(self, request):
        title = request.POST.get('title')
        description = request.POST.get('description')
        publish_date = request.POST.get('publish_date')
        image = request.FILES.get('image')

        News.objects.create(
            title=title,
            description=description,
            publish_date=publish_date,
            feature_image=image  # Make sure this matches your model field
        )
        messages.success(request, 'News submitted successfully.')
        return redirect('/')

# Public-facing preview view (optional)
def preview_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    return render(request, "news/preview.html", {"news": news})

# Public archive/unarchive routes (if needed)
def archive_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    news.archived = True
    news.save()
    ArchivedNews.objects.get_or_create(news=news)
    messages.success(request, 'News archived successfully.')
    return redirect('/admin/news/news/')

def unarchive_news(request, pk):
    news = get_object_or_404(News, pk=pk)
    news.archived = False
    news.save()
    ArchivedNews.objects.filter(news=news).delete()
    messages.success(request, 'News unarchived successfully.')
    return redirect('/admin/news/news/')
