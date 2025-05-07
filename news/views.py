from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import News, NewsLog
from .forms import NewsForm
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required



def news_list(request):
    news_items = News.objects.filter(is_archived=False)
    return render(request, 'news/news_list.html', {'news_items': news_items})


def news_form(request, pk=None):
    instance = get_object_or_404(News, pk=pk) if pk else None
    form = NewsForm(instance=instance)

    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            try:
                with transaction.atomic():
                    news = form.save()
                    action = 'updated' if pk else 'created'

                    # Create log entry with explicit timestamp
                    log = NewsLog.objects.create(
                        news=news,
                        action=action,
                        status='success',
                        message=f'News {action} successfully: {news.title}',
                        timestamp=timezone.now()
                    )
                    print(f"Log created: {log.id} for news: {news.title}")  # Debug print

                messages.success(request, f'News {action} successfully')
                return redirect('news_logs')
            except Exception as e:
                print(f"Error saving news: {str(e)}")  # Debug print
                messages.error(request, f'Error saving news: {str(e)}')

    return render(request, 'news/news_form.html', {'form': form})


@staff_member_required
def news_logs(request):
    active_tab = request.GET.get('tab', 'active')
    base_queryset = NewsLog.objects.select_related('news').order_by('-timestamp')

    if active_tab == 'active':
        logs = base_queryset.filter(news__is_archived=False).distinct()
    else:
        logs = base_queryset.filter(news__is_archived=True).distinct()

    context = {
        'logs': logs,
        'active_tab': active_tab,
        'current_time': timezone.now(),
        'current_user': request.user.username
    }

    return render(request, 'news/news_logs.html', context)


@require_POST
@staff_member_required
def delete_selected_logs(request):
    try:
        log_ids = request.POST.getlist('selected_logs[]')
        deleted_count = NewsLog.objects.filter(id__in=log_ids).delete()[0]

        if deleted_count > 0:
            messages.success(request, f'Successfully deleted {deleted_count} log entries')
        else:
            messages.warning(request, 'No logs were selected for deletion')

        return JsonResponse({
            'status': 'success',
            'message': f'Successfully deleted {deleted_count} log entries'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


def archive_news(request, pk):
    if request.method == 'POST':
        news = get_object_or_404(News, pk=pk)
        try:
            news.is_archived = True
            news.save()

            NewsLog.objects.create(
                news=news,
                action='archived',
                status='success',
                message=f'News archived successfully: {news.title}',
                timestamp=timezone.now()
            )

            messages.success(request, f'News "{news.title}" was archived successfully')
        except Exception as e:
            NewsLog.objects.create(
                news=news,
                action='archived',
                status='failure',
                message=f'Failed to archive news: {news.title}. Error: {str(e)}',
                timestamp=timezone.now()
            )
            messages.error(request, f'Error archiving news: {str(e)}')

    # Redirect back to the same tab
    return redirect(f'{request.META.get("HTTP_REFERER", "/news/logs/")}')
