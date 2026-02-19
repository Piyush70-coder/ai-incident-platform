from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from companies.models import Company


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=255, required=False, help_text="Leave blank if joining existing company")
    company_slug = forms.SlugField(required=False, help_text="Enter company slug if joining existing company")
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400'
    
    def clean(self):
        cleaned_data = super().clean()
        company_slug = cleaned_data.get('company_slug')
        company_name = cleaned_data.get('company_name')
        
        if company_slug and company_name:
            raise forms.ValidationError("Please provide either Company Slug (to join) or Company Name (to create), not both.")
            
        if company_slug:
            if not Company.objects.filter(slug=company_slug).exists():
                self.add_error('company_slug', "Company not found with that slug")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        # Handle company assignment
        company_slug = self.cleaned_data.get('company_slug')
        company_name = self.cleaned_data.get('company_name')
        
        if company_slug:
            # Join existing company
            try:
                company = Company.objects.get(slug=company_slug)
                user.company = company
                user.role = 'engineer'  # Default role for new users
            except Company.DoesNotExist:
                # Should be caught in clean(), but safe fallback
                pass
        elif company_name:
            # Create new company
            company = Company.objects.create(name=company_name)
            user.company = company
            user.role = 'company_admin'  # Creator becomes admin
        else:
            # No company - will be handled by admin
            user.role = 'engineer'
        
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'avatar', 'phone', 'timezone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400'
            }),
            'timezone': forms.Select(attrs={
                'class': 'bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 placeholder-gray-400'
            }, choices=[
                ('UTC', 'UTC'),
                ('America/New_York', 'America/New_York'),
                ('America/Chicago', 'America/Chicago'),
                ('America/Denver', 'America/Denver'),
                ('America/Los_Angeles', 'America/Los_Angeles'),
                ('Europe/London', 'Europe/London'),
                ('Europe/Paris', 'Europe/Paris'),
                ('Asia/Tokyo', 'Asia/Tokyo'),
                ('Asia/Shanghai', 'Asia/Shanghai'),
            ]),
            'avatar': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-400 border border-gray-600 rounded-lg cursor-pointer bg-gray-700 focus:outline-none placeholder-gray-400'
            })
        }

