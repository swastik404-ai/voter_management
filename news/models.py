from django.db import models
from ckeditor.fields import RichTextField


class News(models.Model):
    title = models.CharField(max_length=255)
    feature_image = models.ImageField(upload_to='news/', null=True, blank=True)
    description = RichTextField()
    third_party_link = models.URLField(max_length=200, null=True, blank=True)
    publish_date = models.DateField(auto_now_add=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class ArchivedNews(models.Model):
    news = models.OneToOneField(News, on_delete=models.CASCADE)
    archived_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Archived: {self.news.title}"
