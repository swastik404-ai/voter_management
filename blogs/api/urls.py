from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogViewSet

router = DefaultRouter()
router.register(r'blogs', BlogViewSet, basename='blog')

app_name = 'blog_api'

urlpatterns = [
    path('', include(router.urls)),
]