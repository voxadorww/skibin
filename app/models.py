import random
import string
from django.db import models
from django.utils import timezone
from datetime import timedelta

def generate_paste_id(length=8):
    """Generate a random short ID like Pastebin"""
    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

class Paste(models.Model):
    LANGUAGE_CHOICES = [
        ('plaintext', 'Plain Text'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('csharp', 'C#'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('swift', 'Swift'),
        ('kotlin', 'Kotlin'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('sql', 'SQL'),
        ('bash', 'Bash'),
        ('json', 'JSON'),
        ('yaml', 'YAML'),
        ('markdown', 'Markdown'),
        ('dockerfile', 'Dockerfile'),
    ]
    
    # Short ID like Pastebin
    id = models.CharField(
        primary_key=True,
        max_length=10,
        default=generate_paste_id,
        editable=False
    )
    
    title = models.CharField(max_length=200, blank=True, default='')
    content = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='plaintext')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    views = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        # Ensure we have an ID
        if not self.id:
            self.id = generate_paste_id()
        
        # Set expiry if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=90)
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"{self.title or 'Untitled'} ({self.id})"
    
    @classmethod
    def get_total_pastes(cls):
        """Get total number of pastes (including expired)"""
        return cls.objects.count()
    
    @classmethod
    def get_total_characters(cls):
        """Get total characters shared across all pastes"""
        total = 0
        for paste in cls.objects.all():
            total += len(paste.content)
        return total
    
    @classmethod  
    def get_active_pastes(cls):
        """Get non-expired pastes"""
        return cls.objects.filter(expires_at__gt=timezone.now()).count()