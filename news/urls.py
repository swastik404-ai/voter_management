from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsViewSet, NewsFormView, preview_news, archive_news, unarchive_news

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', NewsFormView.as_view(), name='news_form'),
    path('preview/<int:pk>/', preview_news, name='preview_news'),
    path('archive/<int:pk>/', archive_news, name='archive_news'),
    path('unarchive/<int:pk>/', unarchive_news, name='unarchive_news'),
]
