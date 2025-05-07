from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import NewsViewSet, NewsLogViewSet
from . import views

router = DefaultRouter()
router.register(r'news', NewsViewSet)
router.register(r'news-logs', NewsLogViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('', views.news_list, name='news_list'),
    path('add/', views.news_form, name='news_add'),
    path('edit/<int:pk>/', views.news_form, name='news_edit'),
    path('logs/', views.news_logs, name='news_logs'),
    path('archive/<int:pk>/', views.archive_news, name='archive_news'),
    path('logs/delete-selected/', views.delete_selected_logs, name='delete_selected_logs'),
]