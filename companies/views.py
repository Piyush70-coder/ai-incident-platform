from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Company

@login_required
def company_settings_view(request):
    """
    Manage company settings (Admins only)
    """
    company = request.company
    if not company:
        messages.error(request, "You must be associated with a company.")
        return redirect('profile')
    
    # Permission check
    if not request.user.can_manage_users():
        messages.error(request, "You do not have permission to manage company settings.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        
        if name:
            company.name = name
            company.save()
            messages.success(request, "Company settings updated.")
            return redirect('company_settings')
            
    return render(request, 'companies/settings.html', {'company': company})

@login_required
def company_users_view(request):
    """
    List company users
    """
    company = request.company
    if not company:
        messages.error(request, "You must be associated with a company.")
        return redirect('profile')
        
    users = company.users.all()
    
    return render(request, 'companies/users.html', {'company': company, 'users': users})
