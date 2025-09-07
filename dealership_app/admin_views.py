from django.contrib import admin
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect
from django.urls import reverse


@csrf_protect
@never_cache
def custom_admin_login(request):
    """
    Custom admin login view that redirects to dashboard instead of admin
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '/dashboard/')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active and user.is_staff:
                    login(request, user)
                    # Always redirect to dashboard regardless of next parameter
                    return HttpResponseRedirect('/dashboard/')
                else:
                    messages.error(request, 'Please enter the correct username and password for a staff account.')
            else:
                messages.error(request, 'Please enter the correct username and password for a staff account.')
        else:
            messages.error(request, 'Please enter both username and password.')
    
    # Show login form
    context = {
        'title': 'AUTO DINERO Admin Login',
        'site_title': 'AUTO DINERO Admin',
        'site_header': 'AUTO DINERO Administration',
        'next': request.GET.get('next', '/dashboard/'),
        'error': messages.get_messages(request)
    }
    
    return render(request, 'admin/login.html', context)