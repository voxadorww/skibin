from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db.models import Avg, Count, Q
from .models import Paste
from .forms import PasteForm
import uuid
import time
from datetime import datetime

def home(request):
    """Landing page with stats"""
    total_pastes = Paste.get_total_pastes()
    total_chars = Paste.get_total_characters()
    active_pastes = Paste.get_active_pastes()
    
    # Format numbers nicely
    if total_chars > 1000000:
        chars_display = f"{total_chars / 1000000:.1f}M"
    elif total_chars > 1000:
        chars_display = f"{total_chars / 1000:.1f}K"
    else:
        chars_display = str(total_chars)
    
    # Calculate progress percentage
    if total_pastes > 0:
        paste_progress = (active_pastes / total_pastes) * 100
    else:
        paste_progress = 0
    
    # Calculate average size
    if total_pastes > 0:
        avg_size = total_chars / total_pastes
    else:
        avg_size = 0
    
    context = {
        'current_year': datetime.now().year,
        'total_pastes': total_pastes,
        'total_chars': total_chars,
        'chars_display': chars_display,
        'active_pastes': active_pastes,
        'paste_progress': paste_progress,  # Add this
        'avg_size': avg_size,  # Add this
    }
    return render(request, 'home.html', context)

def contact(request):
    return render(request, "contact.html")

def terms(request):
    return render(request, "terms.html")

@require_http_methods(["GET", "POST"])
def create_paste(request):
    """Create a new paste"""
    if request.method == 'POST':
        form = PasteForm(request.POST)
        if form.is_valid():
            paste = form.save()
            # Redirect to the new paste
            return redirect('view_paste', paste_id=paste.id)  # No str() needed now
    else:
        form = PasteForm()
    
    return render(request, 'new.html', {'form': form})

def view_paste(request, paste_id):
    """View a specific paste"""
    try:
        paste = get_object_or_404(Paste, id=paste_id)
        
        if paste.is_expired():
            raise Http404("This paste has expired")
        
        content_lines = paste.content.split('\n')
        
        paste.views += 1
        paste.save(update_fields=['views'])
        
        return render(request, 'view.html', {
            'paste': paste,
            'content_lines': content_lines,
            'is_code': paste.language != 'plaintext',
        })
        
    except Exception:
        raise Http404("Paste not found")

def raw_paste(request, paste_id):
    """Get raw paste content"""
    paste = get_object_or_404(Paste, id=paste_id)
    
    if paste.is_expired():
        raise Http404("This paste has expired")
    
    response = HttpResponse(paste.content, content_type='text/plain; charset=utf-8')
    response['X-Content-Type-Options'] = 'nosniff'
    return response

def clone_paste(request, paste_id):
    """Clone an existing paste"""
    original = get_object_or_404(Paste, id=paste_id)
    
    if original.is_expired():
        raise Http404("This paste has expired")
    
    form = PasteForm(initial={
        'title': f"Copy of {original.title}" if original.title else "",
        'content': original.content,
        'language': original.language,
    })
    
    return render(request, 'new.html', {
        'form': form,
        'cloning': True,
    })

@require_GET
def health_check(request):
    """Simple health check endpoint"""
    start_time = time.time()
    
    # Check database connection
    try:
        from .models import UptimeLog
        UptimeLog.objects.count()
        db_healthy = True
    except:
        db_healthy = False
    
    response_time = (time.time() - start_time) * 1000
    
    return JsonResponse({
        'status': 'healthy' if db_healthy else 'unhealthy',
        'timestamp': timezone.now().isoformat(),
        'response_time_ms': round(response_time, 2),
        'services': {
            'database': 'healthy' if db_healthy else 'unhealthy',
            'web': 'healthy'
        }
    })

@require_GET
def db_health(request):
    """Database health check"""
    start_time = time.time()
    
    try:
        from .models import UptimeLog
        # Simple query to test DB
        count = UptimeLog.objects.count()
        db_healthy = True
    except Exception as e:
        db_healthy = False
        error = str(e)
    
    response_time = (time.time() - start_time) * 1000
    
    return JsonResponse({
        'status': 'healthy' if db_healthy else 'unhealthy',
        'database': 'connected' if db_healthy else 'disconnected',
        'response_time_ms': round(response_time, 2),
        'timestamp': timezone.now().isoformat()
    })

def status_data(request):
    """API endpoint for status page data"""
    from .models import ServiceStatus, UptimeLog, IncidentUpdate
    from django.db.models import Count, Avg, Q, F, ExpressionWrapper, fields
    from django.db.models.functions import TruncHour, TruncDay
    
    # Get current incidents
    active_incidents = ServiceStatus.objects.filter(
        is_resolved=False
    ).order_by('-start_time')
    
    # Get recent incidents (last 90 days)
    ninety_days_ago = timezone.now() - timezone.timedelta(days=90)
    recent_incidents = ServiceStatus.objects.filter(
        start_time__gte=ninety_days_ago
    ).order_by('-start_time')
    
    # Calculate uptime stats
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    
    # For each service
    services_stats = {}
    for service in ['web', 'api', 'db']:
        logs = UptimeLog.objects.filter(
            service=service,
            checked_at__gte=thirty_days_ago
        )
        
        total_checks = logs.count()
        up_checks = logs.filter(is_up=True).count()
        
        uptime_percent = (up_checks / total_checks * 100) if total_checks > 0 else 100
        avg_response = logs.filter(is_up=True).aggregate(Avg('response_time'))['response_time__avg'] or 0
        
        services_stats[service] = {
            'uptime': round(uptime_percent, 2),
            'avg_response_time': round(avg_response, 2),
            'total_checks': total_checks,
            'up_checks': up_checks,
            'down_checks': total_checks - up_checks,
        }
    
    # Overall uptime (average of all services)
    overall_uptime = sum(stats['uptime'] for stats in services_stats.values()) / len(services_stats)
    
    # Get incident updates
    incident_updates = []
    for incident in recent_incidents:
        updates = incident.updates.all().order_by('created_at')
        incident_updates.extend([
            {
                'incident_id': incident.id,
                'service': incident.get_service_display(),
                'status': update.get_status_display(),
                'message': update.message,
                'time': update.created_at.isoformat(),
                'is_resolved': incident.is_resolved
            }
            for update in updates
        ])
    
    # Sort updates by time
    incident_updates.sort(key=lambda x: x['time'], reverse=True)
    
    return JsonResponse({
        'status': {
            'overall': 'operational' if not active_incidents.exists() else 'issues',
            'services': services_stats,
            'overall_uptime': round(overall_uptime, 2),
            'incidents_this_month': recent_incidents.filter(
                start_time__gte=timezone.now().replace(day=1)
            ).count(),
            'active_incidents': [
                {
                    'id': incident.id,
                    'service': incident.get_service_display(),
                    'status': incident.get_status_display(),
                    'message': incident.message,
                    'start_time': incident.start_time.isoformat(),
                    'duration': str(timezone.now() - incident.start_time) if not incident.is_resolved else None
                }
                for incident in active_incidents
            ]
        },
        'recent_incidents': [
            {
                'id': incident.id,
                'service': incident.get_service_display(),
                'status': incident.get_status_display(),
                'message': incident.message,
                'start_time': incident.start_time.isoformat(),
                'end_time': incident.end_time.isoformat() if incident.end_time else None,
                'duration': str(incident.end_time - incident.start_time) if incident.end_time else None,
                'is_resolved': incident.is_resolved,
                'updates': [
                    {
                        'message': update.message,
                        'time': update.created_at.isoformat(),
                        'status': update.get_status_display()
                    }
                    for update in incident.updates.all().order_by('created_at')
                ]
            }
            for incident in recent_incidents
        ],
        'metrics': {
            'avg_response_time_all': round(
                UptimeLog.objects.filter(
                    is_up=True,
                    checked_at__gte=thirty_days_ago
                ).aggregate(Avg('response_time'))['response_time__avg'] or 0,
                1
            ),
            'total_checks_24h': UptimeLog.objects.filter(
                checked_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).count(),
            'downtime_minutes_30d': UptimeLog.objects.filter(
                is_up=False,
                checked_at__gte=thirty_days_ago
            ).count() * 1,  # Assuming 1 minute checks
        },
        'last_updated': timezone.now().isoformat()
    })
