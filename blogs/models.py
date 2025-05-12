from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.utils import timezone
import uuid


class Blog(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived')
    )

    CATEGORY_CHOICES = (
        ('blog', 'Blog'),
        ('insight', 'Insight')
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        editable=False
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blogs'
    )  # Remove editable=False
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    content = RichTextField()
    summary = models.TextField(max_length=500)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='blog')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    tags = models.CharField(max_length=200, blank=True, help_text="Enter tags separated by commas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=100, editable=False)
    created_time = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog'
        verbose_name_plural = 'Blogs'

    def __str__(self):
        return self.title

    def generate_unique_slug(self):
        base_slug = slugify(self.title)
        unique_slug = base_slug

        while Blog.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"

        return unique_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug()

        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()

        super().save(*args, **kwargs)