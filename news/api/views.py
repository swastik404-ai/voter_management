from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from ..models import News, NewsLog
from .serializers import NewsSerializer, NewsLogSerializer


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

    def perform_create(self, serializer):
        news = serializer.save()
        NewsLog.objects.create(
            news=news,
            action='created',
            status='success',
            message='News item created successfully'
        )

    def perform_update(self, serializer):
        news = serializer.save()
        NewsLog.objects.create(
            news=news,
            action='updated',
            status='success',
            message='News item updated successfully'
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        news = self.get_object()
        news.is_archived = True
        news.save()

        NewsLog.objects.create(
            news=news,
            action='archived',
            status='success',
            message='News item archived successfully'
        )

        return Response({'status': 'archived'})


class NewsLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsLog.objects.all()
    serializer_class = NewsLogSerializer