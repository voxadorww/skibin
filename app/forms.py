from django import forms
from .models import Paste

class PasteForm(forms.ModelForm):
    class Meta:
        model = Paste
        fields = ['title', 'content', 'language']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full p-4 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pink-400 focus:border-transparent outline-none text-lg',
                'placeholder': 'config.py, notes.txt, etc',
                'id': 'paste-title'  # ADD THIS
            }),
            'content': forms.Textarea(attrs={
                'class': 'code-editor',
                'rows': 15,
                'placeholder': '// paste your code here...\n// or just type some text idc',
                'spellcheck': 'false',
                'id': 'code-input'  # ADD THIS
            }),
            'language': forms.Select(attrs={
                'class': 'w-full p-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pink-400 focus:border-transparent outline-none appearance-none',
                'id': 'language-select'  # ADD THIS
            }),
        }