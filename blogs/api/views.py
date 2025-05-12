from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.utils import timezone
from ..models import Blog
from .serializers import BlogSerializer, BlogListSerializer


class BlogViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return BlogListSerializer
        return BlogSerializer

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            created_by=self.request.user.username,
            created_time=timezone.now()
        )

    def get_queryset(self):
        queryset = Blog.objects.all()
        status_param = self.request.query_params.get('status', None)
        category = self.request.query_params.get('category', None)

        if status_param:
            queryset = queryset.filter(status=status_param)
        if category:
            queryset = queryset.filter(category=category)

        return queryset.filter(author=self.request.user)  # Only return user's own blogs

    @action(detail=True, methods=['post'])
    def archive(self, request, slug=None):
        blog = self.get_object()
        blog.status = 'archived'
        blog.save()
        return Response({
            'status': 'success',
            'message': 'Blog archived successfully',
            'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    @action(detail=True, methods=['post'])
    def publish(self, request, slug=None):
        blog = self.get_object()
        blog.status = 'published'
        blog.published_date = timezone.now()
        blog.save()
        return Response({
            'status': 'success',
            'message': 'Blog published successfully',
            'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    @action(detail=True, methods=['get'])
    def preview(self, request, slug=None):
        blog = self.get_object()
        serializer = self.get_serializer(blog)
        return Response(serializer.data)