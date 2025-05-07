from django import forms
from .models import News
from ckeditor.widgets import CKEditorWidget


class NewsForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())
    publish_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True
    )

    class Meta:
        model = News
        fields = ['title', 'featured_image', 'description',
                  'third_party_link', 'publish_date']

    def clean_publish_date(self):
        date = self.cleaned_data.get('publish_date')
        if not date:
            raise forms.ValidationError("Publish date is required")
        return date

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("Title is required")
        return title