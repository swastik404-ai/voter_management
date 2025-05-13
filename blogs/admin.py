from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404
from .models import Blog
from .forms import BlogForm
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.conf import settings


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    form = BlogForm

    list_display = (
        'title',
        'author',
        'category',
        'status',
        'format_created_at',
        'created_by',
        'display_actions'
    )

    search_fields = ('title', 'content', 'author__username', 'created_by')
    list_filter = ['status', 'category']

    readonly_fields = (
        'slug',
        'created_at',
        'updated_at',
        'created_by',
        'created_time'
    )

    fieldsets = (
        ('Blog Content', {
            'fields': (
                'title',
                'featured_image',
                'content',
                'summary',
            ),
            'classes': ('wide',),
        }),
        ('Classification', {
            'fields': (
                'category',
                'status',
                'tags',
            ),
            'classes': ('wide',),
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                'created_time',
                'created_at',
                'updated_at',
                'slug',
            ),
            'classes': ('collapse',),
        }),
    )

    class Media:
        css = {
            'all': [
                'admin/css/forms.css',
                'admin/css/widgets.css',
                'ckeditor/ckeditor.css',  # Add this line
            ]
        }
        js = [
            'admin/js/jquery.init.js',
            'admin/js/core.js',
            'ckeditor/ckeditor.js',  # Add this line
            'ckeditor/config.js',  # Add this line
        ]

    def display_actions(self, obj):
        """Generate action buttons for each row"""
        if obj and hasattr(obj, 'pk') and obj.pk:
            edit_url = reverse('admin:blogs_blog_change', args=[obj.pk])
            preview_url = reverse('admin:blogs_blog_preview', args=[obj.pk])
            archive_url = reverse('admin:blogs_blog_archive', args=[obj.pk])

            return format_html(
                '''
                <div class="action-buttons" style="white-space: nowrap;">
                    <a class="action-btn edit-btn" href="{}" style="margin-right: 5px; padding: 3px 8px; background: #007bff; color: white; border-radius: 3px; text-decoration: none;">
                        <i class="fas fa-edit"></i> Edit
                    </a>
                    <a class="action-btn preview-btn" href="{}" target="_blank" style="margin-right: 5px; padding: 3px 8px; background: #28a745; color: white; border-radius: 3px; text-decoration: none;">
                        <i class="fas fa-eye"></i> Preview
                    </a>
                    <button onclick="archiveBlog(event, {}, '{}')" class="action-btn archive-btn" style="padding: 3px 8px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer;">
                        <i class="fas fa-archive"></i> Archive
                    </button>
                </div>
                <script>
                    if (!window.archiveBlog) {{
                        window.archiveBlog = function(event, blogId, archiveUrl) {{
                            event.preventDefault();
                            if (confirm('Are you sure you want to archive this blog?')) {{
                                fetch(archiveUrl, {{
                                    method: 'POST',
                                    headers: {{
                                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                                    }}
                                }})
                                .then(response => response.json())
                                .then(data => {{
                                    if (data.status === 'success') {{
                                        const row = event.target.closest('tr');
                                        const statusCell = row.querySelector('td.field-status');
                                        if (statusCell) statusCell.textContent = 'Archived';

                                        const messages = document.createElement('div');
                                        messages.className = 'messages';
                                        messages.innerHTML = '<ul class="messagelist"><li class="success">' + data.message + '</li></ul>';
                                        document.querySelector('#content').insertBefore(messages, document.querySelector('.content'));

                                        setTimeout(() => messages.remove(), 3000);
                                    }}
                                }});
                            }}
                        }}
                    }}
                </script>
                ''',
                edit_url, preview_url, obj.pk, archive_url
            )
        return ""

    display_actions.short_description = 'Actions'
    display_actions.allow_tags = True

    def format_created_at(self, obj):
        """Format the created_at date"""
        if obj.created_at:
            return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return "-"

    format_created_at.short_description = 'Created At'

    def archive_blog(self, request, pk):
        """Archive the blog post"""
        if request.method == 'POST':
            blog = get_object_or_404(Blog, pk=pk)
            blog.status = 'archived'
            blog.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Blog archived successfully'
            })
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=400)

    def preview_blog(self, request, pk):
        """Preview view for blog posts"""
        blog = get_object_or_404(Blog, pk=pk)

        # Get the current timezone-aware datetime
        current_time = timezone.now()

        context = {
            'blog': blog,
            'title': f'Preview: {blog.title}',
            'is_popup': True,
            'has_permission': True,
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'opts': self.model._meta,
            'current_datetime': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'user_login': request.user.username,
            'media_url': settings.MEDIA_URL,
            # Debug information
            'debug_image_url': blog.featured_image.url if blog.featured_image else None,
            'debug_image_path': blog.featured_image.path if blog.featured_image else None,
        }

        return render(request, 'admin/blogs/blog/preview.html', context)

    def get_urls(self):
        """Define custom URLs"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/preview/',
                self.admin_site.admin_view(self.preview_blog),
                name='blogs_blog_preview',
            ),
            path(
                '<int:pk>/archive/',
                self.admin_site.admin_view(self.archive_blog),
                name='blogs_blog_archive',
            ),
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.author = request.user
            obj.created_by = request.user.username
            obj.created_time = timezone.now()
        super().save_model(request, obj, form, change)




    def changelist_view(self, request, extra_context=None):
        """Add extra context to the changelist view"""
        extra_context = extra_context or {}
        extra_context['current_datetime'] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        extra_context['user_login'] = request.user.username
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        """Customize the queryset shown in the admin"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(author=request.user)

