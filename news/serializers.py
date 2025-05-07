from rest_framework import serializers
from .models import News, ArchivedNews

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'

class ArchivedNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivedNews
        fields = '__all__'