from django.db import models
from django.utils import timezone
from ckeditor.fields import RichTextField


class News(models.Model):
    title = models.CharField(max_length=200)
    featured_image = models.ImageField(upload_to='news/images/')
    description = RichTextField()
    third_party_link = models.URLField(blank=True, null=True)
    publish_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-publish_date']
        verbose_name = 'News'
        verbose_name_plural = 'News'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Only create log if _skip_log is not set (prevents duplicate logs)
        should_create_log = not hasattr(self, '_skip_log')
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if should_create_log:
            action = 'created' if is_new else 'updated'
            NewsLog.objects.create(
                news=self,
                action=action,
                status='success',
                message=f'News {action} successfully: {self.title}',
                timestamp=timezone.now()
            )


class NewsLog(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(
        max_length=50,
        choices=[
            ('created', 'Created'),
            ('updated', 'Updated'),
            ('archived', 'Archived')
        ]
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ('success', 'Success'),
            ('failure', 'Failure')
        ]
    )
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'News Log'
        verbose_name_plural = 'News Logs'

    def __str__(self):
        return f"{self.news.title} - {self.action} - {self.timestamp}"