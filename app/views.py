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

def status_page(request):
    return render(request, "status.html")

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
