from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('featured_image', models.ImageField(upload_to='news/images/')),
                ('description', models.TextField()),  # Changed from RichTextField for initial migration
                ('third_party_link', models.URLField(blank=True, null=True)),
                ('publish_date', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_archived', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'News',
                'ordering': ['-publish_date'],
            },
        ),
        migrations.CreateModel(
            name='NewsLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=50)),
                ('status', models.CharField(max_length=50)),
                ('message', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('news', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='news.news')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]