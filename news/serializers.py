from rest_framework import serializers
from .models import News, NewsLog

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'
        read_only_fields = ('publish_date',)

class NewsLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsLog
        fields = '__all__'
        read_only_fields = ('created_at',)