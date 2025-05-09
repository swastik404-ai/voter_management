from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404
from .models import Blog
from .forms import BlogForm


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    form = BlogForm

    # Display fields in the list view
    list_display = (
        'title',
        'author',
        'category',
        'status',
        'format_created_at',
        'created_by',
        'display_actions'  # Changed from get_actions to display_actions
    )

    search_fields = ('title', 'content', 'author__username', 'created_by')
    list_filter = []  # Remove sidebar filters

    readonly_fields = (
        'slug',
        'created_at',
        'updated_at',
        'created_by',
        'created_time'
    )

    fieldsets = (
        ('Content', {
            'fields': (
                'title',
                'featured_image',
                'content',
                'summary'
            ),
        }),
        ('Classification', {
            'fields': (
                'category',
                'status',
                'tags'
            ),
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                'created_time',
                'created_at',
                'updated_at',
                'slug'
            ),
            'classes': ('collapse',)
        }),
    )

    def display_actions(self, obj):
        """Generate action buttons for each row"""
        if obj and hasattr(obj, 'pk') and obj.pk:
            edit_url = reverse('admin:blogs_blog_change', args=[obj.pk])
            preview_url = f'/admin/blogs/blog/{obj.pk}/preview/'
            return format_html(
                '<div class="action-buttons">'
                '<a class="action-btn edit-btn" href="{}">'
                '<i class="fas fa-edit"></i> Edit</a> '
                '<a class="action-btn preview-btn" href="{}" target="_blank">'
                '<i class="fas fa-eye"></i> Preview</a>'
                '</div>',
                edit_url, preview_url
            )
        return ""

    display_actions.short_description = 'Actions'
    display_actions.allow_tags = True

    def format_created_at(self, obj):
        """Format the created_at date in the specified format"""
        if obj.created_at:
            return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return "-"

    format_created_at.short_description = 'Created At'
    format_created_at.admin_order_field = 'created_at'

    def save_model(self, request, obj, form, change):
        """Handle saving the model and setting automatic fields"""
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

    def preview_blog(self, request, pk):
        """Preview view for blog posts"""
        blog = get_object_or_404(Blog, pk=pk)
        return render(request, 'admin/blogs/blog/preview.html', {
            'blog': blog,
            'title': f'Preview: {blog.title}'
        })

    def get_urls(self):
        """Define custom URLs"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/preview/',
                self.admin_site.admin_view(self.preview_blog),
                name='blog-preview',
            ),
        ]
        return custom_urls + urls