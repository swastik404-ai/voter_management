from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .models import News, NewsLog


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'publish_date', 'is_archived', 'created_at')
    list_filter = ('is_archived', 'publish_date')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

    def response_add(self, request, obj, post_url_continue=None):
        """
        Override the response after adding a new object to redirect to news logs
        """
        # Create success log entry
        NewsLog.objects.create(
            news=obj,
            action='created',
            status='success',
            message=f'News created successfully: {obj.title}',
            timestamp=timezone.now()
        )

        messages.success(request, f'News "{obj.title}" was created successfully')
        return redirect('news_logs')

    def response_change(self, request, obj):
        """
        Override the response after changing an existing object to redirect to news logs
        """
        # Create update log entry
        NewsLog.objects.create(
            news=obj,
            action='updated',
            status='success',
            message=f'News updated successfully: {obj.title}',
            timestamp=timezone.now()
        )

        messages.success(request, f'News "{obj.title}" was updated successfully')
        return redirect('news_logs')

    def save_model(self, request, obj, form, change):
        """
        Override save_model to prevent duplicate log creation
        """
        obj._skip_log = True  # Skip automatic log creation in model
        super().save_model(request, obj, form, change)


@admin.register(NewsLog)
class NewsLogAdmin(admin.ModelAdmin):
    list_display = ('get_news_title', 'action', 'status', 'formatted_timestamp', 'message')
    list_filter = ('action', 'status', 'timestamp', 'news__is_archived')
    search_fields = ('news__title', 'message')
    readonly_fields = ('news', 'action', 'status', 'message', 'timestamp')
    ordering = ('-timestamp',)

    def get_news_title(self, obj):
        return obj.news.title

    get_news_title.short_description = 'News Title'

    def formatted_timestamp(self, obj):
        return obj.timestamp.strftime("%Y-%m-d H:i:s")

    formatted_timestamp.short_description = 'Timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False