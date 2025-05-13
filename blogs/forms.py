from django import forms
from .models import Blog
from ckeditor.widgets import CKEditorWidget
from django.conf import settings
from ckeditor_uploader.widgets import CKEditorUploadingWidget


class BlogForm(forms.ModelForm):
    content = forms.CharField(
        widget=CKEditorUploadingWidget(config_name='full_editor'),
        required=True
    )

    summary = forms.CharField(
        widget=CKEditorUploadingWidget(config_name='full_editor'),
        required=True
    )


    class Meta:
        model = Blog
        fields = [
            'title',
            'featured_image',
            'content',
            'summary',
            'category',
            'status',
            'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter blog title',
                'style': 'width: 100%; padding: 8px; margin-bottom: 10px;'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tags separated by commas',
                'style': 'width: 100%; padding: 8px;'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%; padding: 0px;'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%; padding: 0px;'
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'form-control',
                'style': 'width: 100%; padding: 8px;'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add labels and help text
        self.fields['title'].help_text = 'Enter a descriptive title for your blog post'
        self.fields['featured_image'].help_text = 'Upload an image to be displayed at the top of your blog post'
        self.fields['tags'].help_text = 'Enter tags separated by commas (e.g., technology, programming, python)'
        self.fields['category'].help_text = 'Select the category that best fits your blog post'
        self.fields['status'].help_text = 'Set the current status of your blog post'