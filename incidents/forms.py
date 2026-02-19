from django import forms
from .models import Incident, IncidentComment, IncidentLog


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True
        super().__init__(attrs)


class IncidentForm(forms.ModelForm):
    affected_services = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Comma-separated services (e.g., API, Database, Cache)'
            }
        ),
        help_text='Enter comma-separated services; e.g., API, Database, Cache'
    )
    # log_files handled directly from request.FILES in the view
    
    class Meta:
        model = Incident
        fields = [
            'title', 'description', 'severity', 'category',
            'affected_services', 'assigned_to', 'scheduled_for'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'affected_services': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Comma-separated services (e.g., API, Database, Cache)'
                }
            ),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_for': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if company:
            self.fields['assigned_to'].queryset = company.users.all()
            self.fields['assigned_to'].required = False
        
        if 'scheduled_for' in self.fields:
            self.fields['scheduled_for'].input_formats = ['%Y-%m-%dT%H:%M']
    
    # File validation is performed in the view when iterating request.FILES.getlist('log_files')
    
    def clean_affected_services(self):
        services = self.cleaned_data.get('affected_services', '')
        if isinstance(services, str):
            # Convert comma-separated string to list
            services_list = [s.strip() for s in services.split(',') if s.strip()]
            return services_list
        return services or []


class IncidentCommentForm(forms.ModelForm):
    class Meta:
        model = IncidentComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Add a comment...'})
        }


class IncidentLogForm(forms.ModelForm):
    class Meta:
        model = IncidentLog
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.txt,.log,.zip,.tar.gz'})
        }
