# monitoring.py - Run this as a background task (cron every 1 minute)
import requests
import time
from django.utils import timezone
from django.db import transaction
from .models import UptimeLog, ServiceStatus

def check_service(url, service_name, timeout=10):
    """Check if a service is up and log the result"""
    start_time = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        is_up = response.status_code == 200
        
        # Log the check
        UptimeLog.objects.create(
            service=service_name,
            is_up=is_up,
            response_time=response_time
        )
        
        # Check if we need to create/update an incident
        if not is_up:
            create_incident_if_needed(service_name)
        else:
            resolve_incident_if_up(service_name)
            
        return is_up, response_time
        
    except requests.RequestException as e:
        response_time = (time.time() - start_time) * 1000
        
        UptimeLog.objects.create(
            service=service_name,
            is_up=False,
            response_time=response_time
        )
        
        create_incident_if_needed(service_name)
        return False, response_time

def create_incident_if_needed(service_name):
    """Create an incident if service is down and no active incident exists"""
    with transaction.atomic():
        # Check for existing unresolved incident
        existing = ServiceStatus.objects.filter(
            service=service_name,
            is_resolved=False
        ).first()
        
        if not existing:
            ServiceStatus.objects.create(
                service=service_name,
                status='major',
                message=f'{service_name} is not responding',
                start_time=timezone.now()
            )

def resolve_incident_if_up(service_name):
    """Mark incident as resolved if service is back up"""
    with transaction.atomic():
        incident = ServiceStatus.objects.filter(
            service=service_name,
            is_resolved=False
        ).first()
        
        if incident:
            incident.is_resolved = True
            incident.end_time = timezone.now()
            incident.status = 'operational'
            incident.save()
            
            # Add resolution update
            IncidentUpdate.objects.create(
                incident=incident,
                status='operational',
                message=f'{service_name} is back online'
            )

def check_all_services():
    """Check all skibin.lol services"""
    services_to_check = {
        'web': 'https://skibin.lol/',
        'api': 'https://skibin.lol/api/health',  # You'll need to create this
        'db': 'https://skibin.lol/api/db-health',  # You'll need to create this
    }
    
    results = {}
    for service_name, url in services_to_check.items():
        is_up, response_time = check_service(url, service_name)
        results[service_name] = {
            'is_up': is_up,
            'response_time': response_time
        }
    
    # Check overall status
    all_up = all(result['is_up'] for result in results.values())
    if not all_up and not ServiceStatus.objects.filter(service='all', is_resolved=False).exists():
        ServiceStatus.objects.create(
            service='all',
            status='partial',
            message='Some services are experiencing issues',
            start_time=timezone.now()
        )
    
    return results

# For cron: python manage.py shell -c "from your_app.monitoring import check_all_services; check_all_services()"
