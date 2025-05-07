from rest_framework import serializers
from ..models import News, NewsLog

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'featured_image', 'description',
                 'third_party_link', 'publish_date', 'is_archived']

class NewsLogSerializer(serializers.ModelSerializer):
    news_title = serializers.CharField(source='news.title', read_only=True)

    class Meta:
        model = NewsLog
        fields = ['id', 'news_title', 'action', 'status', 'message', 'timestamp']