from rest_framework import serializers
from ..models import Blog


class BlogSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    created_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    slug = serializers.SlugField(read_only=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)  # Make author read-only

    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'author', 'author_name', 'featured_image',
            'content', 'summary', 'category', 'status', 'tags',
            'created_at', 'updated_at', 'published_date', 'created_by', 'created_time'
        ]
        read_only_fields = [
            'slug', 'author', 'created_at', 'updated_at',
            'created_by', 'created_time'
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username


class BlogListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = ['id', 'title', 'slug', 'summary', 'status', 'category', 'created_at', 'author_name']
        read_only_fields = ['slug', 'author_name']

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username