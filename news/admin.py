from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.shortcuts import redirect, get_object_or_404, render

from .models import News, ArchivedNews

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'short_description_html', 'publish_date', 'is_archived', 'action_buttons')
    list_filter = ('archived',)
    actions = ['archive_selected']

    def short_description_html(self, obj):
        return mark_safe(obj.description[:100] + '...')
    short_description_html.short_description = 'Description'

    def is_archived(self, obj):
        return obj.archived
    is_archived.boolean = True
    is_archived.short_description = 'Archived'

    def action_buttons(self, obj):
        preview_url = reverse('admin:news_news_preview', args=[obj.pk])
        archive_url = reverse('admin:news_news_archive', args=[obj.pk]) if not obj.archived else reverse('admin:news_news_unarchive', args=[obj.pk])
        archive_label = 'Unarchive' if obj.archived else 'Archive'
        return format_html(
            f'<a class="button" href="{preview_url}">Preview</a>&nbsp;'
            f'<a class="button" href="{reverse("admin:news_news_change", args=[obj.pk])}">Edit</a>&nbsp;'
            f'<a class="button" href="{archive_url}">{archive_label}</a>'
        )
    action_buttons.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('news/preview/<int:pk>/', self.admin_site.admin_view(self.preview_news), name='news_news_preview'),
            path('news/archive/<int:pk>/', self.admin_site.admin_view(self.archive_news), name='news_news_archive'),
            path('news/unarchive/<int:pk>/', self.admin_site.admin_view(self.unarchive_news), name='news_news_unarchive'),
        ]
        return custom_urls + urls

    def preview_news(self, request, pk):
        news_item = get_object_or_404(News, pk=pk)
        return render(request, 'admin/news/preview.html', {'news': news_item})

    def archive_news(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.archived = True
        news.save()
        ArchivedNews.objects.get_or_create(news=news)
        return redirect('admin:news_news_changelist')

    def unarchive_news(self, request, pk):
        news = get_object_or_404(News, pk=pk)
        news.archived = False
        news.save()
        ArchivedNews.objects.filter(news=news).delete()
        return redirect('admin:news_news_changelist')

    def archive_selected(self, request, queryset):
        for news in queryset:
            news.archived = True
            news.save()
            ArchivedNews.objects.get_or_create(news=news)
        self.message_user(request, f"{queryset.count()} news item(s) archived.")
    archive_selected.short_description = "Archive selected news"

@admin.register(ArchivedNews)
class ArchivedNewsAdmin(admin.ModelAdmin):
    list_display = ('news', 'archived_at')
