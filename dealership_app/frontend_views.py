import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.utils import translation
from django.urls import reverse
from .models import Car, CarBrand, CarModel

def index(request):
    # Get first 8 cars based on position (custom order)
    featured_cars = Car.objects.filter(sold=False).order_by('position', '-created_at')[:8]
    # Only show brands that have available cars
    brands = CarBrand.objects.filter(car__sold=False).distinct().order_by('name')
    
    # Get current language
    current_language = translation.get_language()
    
    # Get only fuel choices that exist in available cars for the search form
    base_qs = Car.objects.filter(sold=False)
    available_fuels = base_qs.values_list('fuel_type', flat=True).distinct()
    fuel_choices = [(key, label) for key, label in Car.get_fuel_choices(current_language) if key in available_fuels]
    
    return render(request, 'frontend/index.html', {
        'featured_cars': featured_cars,
        'brands': brands,
        'fuel_choices': fuel_choices,
    })

def ajax_models(request):
    """Return JSON list of {id,name} for models of given brand that have available cars."""
    brand_id = request.GET.get('brand')
    models = []
    if brand_id and brand_id.isdigit():
        # Only show models that have available cars for this brand
        qs = CarModel.objects.filter(
            brand_id=brand_id,
            car__sold=False
        ).distinct().order_by('name')
        models = [{'id': m.id, 'name': m.name} for m in qs]
    return JsonResponse(models, safe=False)

def vehicle_list(request):
    base_qs = Car.objects.filter(sold=False)
    qs = base_qs

    # -- Filters --
    brand       = request.GET.get('brand')
    model_id    = request.GET.get('model_name') or request.GET.get('model')
    trans       = request.GET.get('transmission')
    body        = request.GET.get('vehicle_body') or request.GET.get('body_type')
    fuel        = request.GET.get('fuel')
    color       = request.GET.get('color')
    beginners   = request.GET.get('for_beginners')
    price_from  = request.GET.get('price_from')
    price_to    = request.GET.get('price_to')
    year_from   = request.GET.get('year_from')
    
    # New sorting options
    sort_price   = request.GET.get('sort_price')
    sort_mileage = request.GET.get('sort_mileage')  
    sort_year    = request.GET.get('sort_year')

    # Track if any filters are applied
    filters_applied = any([brand, model_id, trans, body, fuel, color, beginners, 
                          price_from, price_to, year_from])

    if brand:
        qs = qs.filter(brand_id=brand)
    if model_id:
        qs = qs.filter(model_name_id=model_id)
    if trans:
        qs = qs.filter(transmission=trans)
    if body:
        qs = qs.filter(body_type=body)
    if fuel:
        qs = qs.filter(fuel_type=fuel)
    if color:
        qs = qs.filter(color=color)
    if beginners:
        qs = qs.filter(kilowatts__lte=77)
    
    # Price range filtering
    if price_from and price_from.isdigit():
        qs = qs.filter(price__gte=int(price_from))
    if price_to and price_to.isdigit():
        qs = qs.filter(price__lte=int(price_to))
    
    # Year filtering
    if year_from and year_from.isdigit():
        qs = qs.filter(year__gte=int(year_from))

    # If filters applied but no results, show all cars
    if filters_applied and not qs.exists():
        qs = base_qs
        no_results_fallback = True
    else:
        no_results_fallback = False

    # -- Sorting --
    if sort_price in ['asc','desc']:
        qs = qs.order_by('price' if sort_price=='asc' else '-price')
    elif sort_mileage in ['asc','desc']:
        qs = qs.order_by('mileage' if sort_mileage=='asc' else '-mileage')
    elif sort_year in ['asc','desc']:
        qs = qs.order_by('year' if sort_year=='asc' else '-year')
    else:
        # Default sorting by position (custom order), then by creation date
        qs = qs.order_by('position', '-created_at')

    # -- Pagination --
    paginator = Paginator(qs, 12)  # Show 12 cars per page
    page = request.GET.get('page')
    cars = paginator.get_page(page)

    # models for the initial brand - only show models with available cars
    models_qs = CarModel.objects.filter(
        brand_id=brand,
        car__sold=False
    ).distinct().order_by('name') if brand else []

    # Get current language
    current_language = translation.get_language()
    
    # Get only choices that exist in available cars
    available_transmissions = base_qs.values_list('transmission', flat=True).distinct()
    transmission_choices = [(key, label) for key, label in Car.get_transmission_choices(current_language) if key in available_transmissions]
    
    available_fuels = base_qs.values_list('fuel_type', flat=True).distinct()
    fuel_choices = [(key, label) for key, label in Car.get_fuel_choices(current_language) if key in available_fuels]
    
    available_bodies = base_qs.values_list('body_type', flat=True).distinct()
    vehicle_bodies = [(key, label) for key, label in Car.get_body_choices(current_language) if key in available_bodies]

    return render(request, 'frontend/vehicles.html', {
        'cars': cars,
        # Only show brands that have available cars
        'brands': CarBrand.objects.filter(car__sold=False).distinct().order_by('name'),
        'models': models_qs,
        'transmission_choices': transmission_choices,
        'fuel_choices':        fuel_choices,
        'vehicle_bodies':      vehicle_bodies,
        'colors':              Car.get_color_choices(current_language),
        'no_results_fallback': no_results_fallback,
    })

def vehicle_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    
    # Get current language
    current_language = translation.get_language()
    
    # Get ALL available cars as recommendations
    recommended_cars = get_recommended_cars(car, limit=None)
    
    context = {
        'car': car,
        'recommended_cars': recommended_cars,
        'current_language': current_language,
    }
    return render(request, 'frontend/vehicle_detail.html', context)


def get_recommended_cars(current_car, limit=None):
    """
    Intelligent recommendation system for similar cars
    Priority: Same brand > Similar price > Same fuel type > Same body type > Newest
    """
    all_cars = Car.objects.filter(sold=False).exclude(pk=current_car.pk)
    
    if not all_cars.exists():
        return []
    
    # Calculate price range (±30%)
    price_min = current_car.price * 0.7
    price_max = current_car.price * 1.3
    
    # Scoring system for recommendations
    scored_cars = []
    
    for car in all_cars:
        score = 0
        
        # Same brand = +50 points
        if car.brand_id == current_car.brand_id:
            score += 50
            
        # Same model = +30 points (if different brand, this won't apply)
        if car.model_name_id == current_car.model_name_id:
            score += 30
        
        # Similar price range (±30%) = +25 points
        if price_min <= car.price <= price_max:
            score += 25
        # Closer price = more points
        else:
            price_diff = abs(car.price - current_car.price)
            max_diff = current_car.price * 0.5  # Max 50% difference
            if price_diff <= max_diff:
                score += max(5, 20 - int(price_diff / (max_diff / 15)))
        
        # Same fuel type = +20 points
        if car.fuel_type == current_car.fuel_type:
            score += 20
            
        # Same body type = +15 points  
        if car.body_type == current_car.body_type:
            score += 15
            
        # Same transmission = +10 points
        if car.transmission == current_car.transmission:
            score += 10
            
        # Similar year (±3 years) = +10 points
        year_diff = abs(car.year - current_car.year)
        if year_diff <= 3:
            score += max(2, 10 - year_diff * 2)
            
        # Similar power (±50kW) = +5 points  
        if abs(car.kilowatts - current_car.kilowatts) <= 50:
            score += 5
            
        # Newer cars get slight bonus = +1-3 points
        score += min(3, (car.year - 2020))
        
        # Better position (lower number) gets bonus points = +1-10 points
        # Position 0-5 gets 10 points, 6-10 gets 8 points, etc.
        if car.position <= 5:
            score += 10
        elif car.position <= 10:
            score += 8
        elif car.position <= 15:
            score += 6
        elif car.position <= 20:
            score += 4
        elif car.position <= 30:
            score += 2
        
        scored_cars.append((car, score))
    
    # Sort by score (descending) and get top recommendations
    scored_cars.sort(key=lambda x: x[1], reverse=True)
    
    # Return just the car objects, limited to requested amount (or all if limit is None)
    if limit is None:
        return [car for car, score in scored_cars]
    else:
        return [car for car, score in scored_cars[:limit]]

def about(request):
    return render(request, 'frontend/about.html')

def contact(request):
    return render(request, 'frontend/contact.html')

def services(request):
    service_type = request.GET.get('service', 'order')  # Default to 'order'
    return render(request, 'frontend/services.html', {
        'service_type': service_type
    })

def collaboration(request):
    return render(request, 'frontend/collaboration.html')

def terms(request):
    return render(request, 'frontend/terms.html')

def privacy(request):
    return render(request, 'frontend/privacy.html')

def custom_404_handler(request, exception):
    """
    Custom 404 handler that redirects to the closest existing page
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

def redirect_to_vehicles(request, invalid):
    """
    Redirect invalid vehicle URLs to the vehicles page
    """
    return redirect(reverse('frontend_vehicles'))

# Specific redirect functions for common typos/variations
def redirect_to_services(request, invalid=None):
    """Redirect to services page"""
    return redirect(reverse('frontend_services'))

def redirect_to_collaboration(request, invalid=None):
    """Redirect to collaboration page"""
    return redirect(reverse('frontend_collaboration'))

def redirect_to_contact(request, invalid=None):
    """Redirect to contact page"""
    return redirect(reverse('frontend_contact'))

def redirect_to_about(request, invalid=None):
    """Redirect to about page"""
    return redirect(reverse('frontend_about'))

def redirect_to_terms(request, invalid=None):
    """Redirect to terms page"""
    return redirect(reverse('frontend_terms'))

def redirect_to_privacy(request, invalid=None):
    """Redirect to privacy page"""
    return redirect(reverse('frontend_privacy'))

def redirect_to_home_if_frontend(request, invalid):
    """
    Redirect to home page, but only if it's not an admin/dashboard URL
    """
    invalid_lower = invalid.lower()
    
    # Don't redirect admin/dashboard URLs - let them 404 properly
    admin_patterns = ['dashboard', 'admin', 'login', 'logout', 'ajax']
    if any(pattern in invalid_lower for pattern in admin_patterns):
        # Let Django handle this normally (will 404)
        from django.http import Http404
        raise Http404("Page not found")
    
    # For everything else, redirect to home
    return redirect(reverse('frontend_index'))
