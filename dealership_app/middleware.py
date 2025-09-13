from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class Custom404RedirectMiddleware(MiddlewareMixin):
    """
    Custom middleware that handles 404 errors and redirects to closest existing page
    Works even when DEBUG=True
    """
    
    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return self.handle_404(request)
        return None
    
    def handle_404(self, request):
        """
        Handle 404 errors by redirecting to the closest existing page
        """
        current_path = request.path_info
        current_language = translation.get_language() or 'en'
        
        # Remove leading/trailing slashes and split path
        path_parts = [p for p in current_path.strip('/').split('/') if p]
        
        # Define valid page mappings with their URL names
        valid_pages = {
            'vehicles': 'frontend_vehicles',
            'services': 'frontend_services', 
            'collaboration': 'frontend_collaboration',
            'about': 'frontend_about',
            'contact': 'frontend_contact',
            'terms': 'frontend_terms',
            'privacy': 'frontend_privacy',
        }
        
        # If path has language prefix, remove it for processing
        if path_parts and path_parts[0] == current_language:
            path_parts = path_parts[1:]
        
        # Strategy 1: Try to match first part of path to valid pages
        if path_parts:
            first_part = path_parts[0].lower()
            
            # Check for exact match
            if first_part in valid_pages:
                return redirect(reverse(valid_pages[first_part]))
            
            # Check for partial matches (e.g., 'vehic' matches 'vehicles')
            for page_name, url_name in valid_pages.items():
                if page_name.startswith(first_part) or first_part.startswith(page_name[:3]):
                    return redirect(reverse(url_name))
        
        # Strategy 2: Check if it's a vehicle detail URL with invalid ID
        if len(path_parts) >= 2 and path_parts[0].lower() == 'vehicles':
            # Redirect to vehicles list page
            return redirect(reverse('frontend_vehicles'))
        
        # Strategy 3: If it's any other multilevel path, redirect to closest parent
        if len(path_parts) >= 2:
            parent_page = path_parts[0].lower()
            if parent_page in valid_pages:
                return redirect(reverse(valid_pages[parent_page]))
        
        # Strategy 4: Check if URL contains common keywords and redirect accordingly
        full_path_lower = current_path.lower()
        if 'vehicle' in full_path_lower or 'car' in full_path_lower:
            return redirect(reverse('frontend_vehicles'))
        elif 'service' in full_path_lower:
            return redirect(reverse('frontend_services'))
        elif 'about' in full_path_lower:
            return redirect(reverse('frontend_about'))
        elif 'contact' in full_path_lower:
            return redirect(reverse('frontend_contact'))
        elif 'collaboration' in full_path_lower or 'partner' in full_path_lower:
            return redirect(reverse('frontend_collaboration'))
        
        # Default: Redirect to home page
        return redirect(reverse('frontend_index'))