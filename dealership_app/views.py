import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Car, CarImage, CarEquipment,CarModel
from .forms import CarModelForm, CarImageForm
import threading
from django.utils import timezone
from django.db.models import Avg, Sum, Count, F, ExpressionWrapper, FloatField, Max
from django.utils import timezone
from django.contrib.auth.decorators import login_required



# ✅ DASHBOARD HOME
def admin_dashboard(request):
    # Check if user is authenticated, if not redirect to admin login
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/?next=/dashboard/')
    total_cars = Car.objects.count()
    total_sold = Car.objects.filter(sold=True).count()

    # 1. Просечна цена на сите возила
    avg_price = Car.objects.aggregate(avg=Avg('price'))['avg'] or 0

    # 2. Просечна цена на продадените
    avg_price_sold = Car.objects.filter(sold=True).aggregate(avg=Avg('price'))['avg'] or 0

    # 3. Вредност на непродадени (инвентарио)
    inventory_value = Car.objects.filter(sold=False).aggregate(total=Sum('price'))['total'] or 0

    # 4. Просечна цена по година на производство
    current_year = timezone.now().year
    age_price_expr = ExpressionWrapper(
        F('price') / (current_year - F('year') + 1),
        output_field=FloatField()
    )
    avg_price_per_year = Car.objects.annotate(age_price=age_price_expr).aggregate(avg=Avg('age_price'))['avg'] or 0

    # 5. Распределба по тип на гориво
    fuel_data = Car.objects.values('fuel_type').annotate(count=Count('id')).order_by()
    fuel_labels = [item['fuel_type'] for item in fuel_data]
    fuel_counts = [item['count'] for item in fuel_data]

    # 6. Latest added cars
    latest_cars = Car.objects.select_related('brand', 'model_name').order_by('-created_at')[:5]
    
    # 7. Calculate available cars for the chart
    available_cars = total_cars - total_sold

    return render(request, "admin_custom/dashboard.html", {
        "total_cars": total_cars,
        "total_sold": total_sold,
        "available_cars": available_cars,
        "avg_price": round(avg_price, 2),
        "avg_price_sold": round(avg_price_sold, 2),
        "inventory_value": inventory_value,
        "avg_price_per_year": round(avg_price_per_year, 2),
        "fuel_labels": fuel_labels,
        "fuel_counts": fuel_counts,
        "latest_cars": latest_cars,
    })



# ✅ LIST CARS
def admin_car_list(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/?next=' + request.path)
    
    # Get filter parameters
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    sort = request.GET.get('sort', '-created_at')
    
    # Base queryset with related objects for optimization
    cars = Car.objects.select_related('brand', 'model_name').all()
    
    # Apply search filter
    if q:
        cars = cars.filter(
            Q(title__icontains=q) |
            Q(brand__name__icontains=q) |
            Q(model_name__name__icontains=q)
        )
    
    # Apply status filter
    if status == 'available':
        cars = cars.filter(sold=False)
    elif status == 'sold':
        cars = cars.filter(sold=True)
    
    # Apply sorting
    if sort:
        if sort == 'brand':
            cars = cars.order_by('brand__name', 'model_name__name')
        elif sort == 'position':
            cars = cars.order_by('position', '-created_at')
        else:
            cars = cars.order_by(sort)
    else:
        # Default sorting by position (custom order), then by creation date
        cars = cars.order_by('position', '-created_at')
    
    # Calculate statistics
    total_cars = Car.objects.count()
    available_cars = Car.objects.filter(sold=False).count()
    sold_cars = Car.objects.filter(sold=True).count()
    avg_price = Car.objects.aggregate(avg=Avg('price'))['avg'] or 0
    
    # Pagination
    paginator = Paginator(cars, 12)  # Show 12 cars per page for better grid layout
    page = request.GET.get('page')
    cars = paginator.get_page(page)
    
    return render(request, 'admin_custom/car_list.html', {
        'cars': cars,
        'q': q,
        'status': status,
        'sort': sort,
        'total_cars': total_cars,
        'available_cars': available_cars,
        'sold_cars': sold_cars,
        'avg_price': round(avg_price, 2),
    })

# ✅ ADD CAR
def admin_car_add(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/?next=' + request.path)
    if request.method == "POST":
        car_form = CarModelForm(request.POST, request.FILES)
        image_form = CarImageForm(request.POST, request.FILES)
        files = request.FILES.getlist("images")

        # Debug: log received files
        print("DEBUG: files sent →", files)

        # **Debug: show form validity and errors**
        is_valid = car_form.is_valid()
        print("DEBUG: car_form.is_valid() →", is_valid)
        if not is_valid:
            print("DEBUG: car_form.errors →", car_form.errors)

        if is_valid:
            car = car_form.save()
            
            # Set equipment after the car is saved and has a primary key
            equipment_ids = request.POST.getlist("equipment")
            if equipment_ids:
                car.equipment.set(equipment_ids)

            # Get the highest position for existing images and add new ones after
            max_position = CarImage.objects.filter(car=car).aggregate(
                max_pos=Max('position')
            )['max_pos'] or 0
            
            for i, f in enumerate(files):
                print(f"DEBUG: saving image → {f}")
                CarImage.objects.create(car=car, image=f, position=max_position + i + 1)

            # Handle AJAX request (for auto-save during image upload)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": True,
                    "car_id": car.id,
                    "message": "Car saved successfully!"
                })
            
            messages.success(request, "✅ Car added successfully!")
            return redirect("admin_car_list")
        else:
            # Handle AJAX request errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "errors": car_form.errors,
                    "message": "Please fix the form errors"
                })
            messages.error(request, "❌ Please fix the errors below.")
    else:
        car_form = CarModelForm()
        image_form = CarImageForm()

    return render(request, "admin_custom/car_form.html", {
        "form": car_form,
        "image_form": image_form,
        "images": [],
        "all_equipment": CarEquipment.objects.all(),
        "selected_equipment": [],
        "initial_model": "",
    })


# ✅ EDIT CAR
def admin_car_edit(request, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/?next=' + request.path)
    car = get_object_or_404(Car, pk=pk)
    images = CarImage.objects.filter(car=car)

    if request.method == "POST":
        car_form = CarModelForm(request.POST, request.FILES, instance=car)
        image_form = CarImageForm(request.POST, request.FILES)
        files = request.FILES.getlist("images")

        # Debug: log received files
        print("DEBUG: files sent →", files)

        # **Debug: show form validity and errors**
        is_valid = car_form.is_valid()
        print("DEBUG: car_form.is_valid() →", is_valid)
        if not is_valid:
            print("DEBUG: car_form.errors →", car_form.errors)

        if is_valid:
            car = car_form.save()
            car.equipment.set(request.POST.getlist("equipment"))

            # Get the highest position for existing images and add new ones after
            max_position = CarImage.objects.filter(car=car).aggregate(
                max_pos=Max('position')
            )['max_pos'] or 0
            
            for i, f in enumerate(files):
                print(f"DEBUG: saving image → {f}")
                CarImage.objects.create(car=car, image=f, position=max_position + i + 1)

            messages.success(request, "✅ Car updated successfully!")
            return redirect("admin_car_edit", pk=car.pk)
        else:
            messages.error(request, "❌ Please fix the errors below.")
    else:
        car_form = CarModelForm(instance=car)
        image_form = CarImageForm()

    return render(request, "admin_custom/car_form.html", {
        "form": car_form,
        "image_form": image_form,
        "car": car,
        "images": images,
        "all_equipment": CarEquipment.objects.all(),
        "selected_equipment": car.equipment.all(),
        "initial_model": car.model_name_id or "",
    })


# ✅ AJAX DELETE IMAGE (No refresh)
def ajax_delete_car_image(request, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        img = get_object_or_404(CarImage, id=pk)
        car_id = img.car.id  # CarImage must have a ForeignKey to Car
        if img.image and os.path.isfile(img.image.path):
            os.remove(img.image.path)
        img.delete()
        remaining = CarImage.objects.filter(car_id=car_id).count()
        return JsonResponse({"success": True, "remaining": remaining})
    return JsonResponse({"success": False}, status=400)

# ✅ AJAX REORDER CAR IMAGES
def ajax_reorder_car_images(request):
    """AJAX endpoint to reorder car images via drag-and-drop"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)
    
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            import json
            data = json.loads(request.body)
            image_ids = data.get('image_ids', [])
            
            if not image_ids:
                return JsonResponse({"success": False, "error": "No image IDs provided"})
            
            # Update the position field for each image based on the new order
            images_to_update = []
            for index, image_id in enumerate(image_ids):
                try:
                    image = CarImage.objects.get(id=image_id)
                    image.position = index + 1  # Start positions from 1
                    images_to_update.append(image)
                except CarImage.DoesNotExist:
                    continue
            
            # Bulk update all positions at once
            if images_to_update:
                CarImage.objects.bulk_update(images_to_update, ['position'])
                return JsonResponse({
                    "success": True, 
                    "message": f"Successfully reordered {len(images_to_update)} images"
                })
            else:
                return JsonResponse({"success": False, "error": "No valid images found to update"})
            
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

# ✅ AJAX ADD NEW EQUIPMENT
def ajax_add_equipment(request):
    """AJAX endpoint to add new equipment"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)
    
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            import json
            data = json.loads(request.body)
            equipment_name = data.get('name', '').strip()
            
            if not equipment_name:
                return JsonResponse({"success": False, "error": "Equipment name is required"})
            
            if len(equipment_name) > 100:
                return JsonResponse({"success": False, "error": "Equipment name must be 100 characters or less"})
            
            # Check if we've reached the 250 equipment limit
            if CarEquipment.objects.count() >= 250:
                return JsonResponse({"success": False, "error": "Maximum of 250 equipment items allowed"})
            
            # Check if equipment already exists (case-insensitive)
            if CarEquipment.objects.filter(name__iexact=equipment_name).exists():
                return JsonResponse({"success": False, "error": "Equipment with this name already exists"})
            
            # Create new equipment
            equipment = CarEquipment.objects.create(name=equipment_name)
            
            return JsonResponse({
                "success": True,
                "equipment": {
                    "id": equipment.id,
                    "name": equipment.name
                },
                "message": f"Equipment '{equipment_name}' added successfully"
            })
            
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

# ✅ DELETE CAR
def admin_car_delete(request, pk):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/?next=' + request.path)
    car = get_object_or_404(Car, pk=pk)
    extra_images = CarImage.objects.filter(car=car)
    for img in extra_images:
        if img.image and os.path.isfile(img.image.path):
            os.remove(img.image.path)
        img.delete()
    if car.main_image and os.path.isfile(car.main_image.path):
        os.remove(car.main_image.path)
    car.delete()
    messages.success(request, "🗑 Car and all its images deleted!")
    return redirect("admin_car_list")

def ajax_load_models(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"error": "Authentication required"}, status=401)
    bid = request.GET.get('brand')
    qs = CarModel.objects.filter(brand_id=bid).values('id','name')
    return JsonResponse(list(qs), safe=False)


# ✅ CAR REORDERING VIEW
def admin_car_reorder(request):
    """Dedicated view for reordering cars with drag-and-drop interface"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/?next=' + request.path)
    
    cars = Car.objects.select_related('brand', 'model_name').order_by('position', '-created_at')
    
    return render(request, 'admin_custom/car_reorder.html', {
        'cars': cars,
        'total_cars': cars.count(),
    })


# ✅ AJAX UPDATE CAR POSITION
def ajax_update_car_position(request):
    """AJAX endpoint to update car positions after drag-and-drop"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"error": "POST method required"}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        car_positions = data.get('positions', [])
        
        # Update positions in bulk
        cars_to_update = []
        for item in car_positions:
            car_id = item.get('id')
            position = item.get('position')
            
            try:
                car = Car.objects.get(id=car_id)
                car.position = position
                cars_to_update.append(car)
            except Car.DoesNotExist:
                continue
        
        # Bulk update for performance
        Car.objects.bulk_update(cars_to_update, ['position'])
        
        return JsonResponse({
            "success": True, 
            "message": f"Successfully updated positions for {len(cars_to_update)} cars"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ✅ BULK POSITION TOOLS
def ajax_bulk_position_tools(request):
    """AJAX endpoints for bulk position operations"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"error": "POST method required"}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'reset_positions':
            # Reset all positions based on creation date
            cars = Car.objects.order_by('-created_at')
            for i, car in enumerate(cars):
                car.position = i
            Car.objects.bulk_update(cars, ['position'])
            
            return JsonResponse({
                "success": True,
                "message": f"Reset positions for {cars.count()} cars based on creation date"
            })
            
        elif action == 'randomize_positions':
            # Randomize positions
            import random
            cars = list(Car.objects.all())
            positions = list(range(len(cars)))
            random.shuffle(positions)
            
            for car, position in zip(cars, positions):
                car.position = position
            Car.objects.bulk_update(cars, ['position'])
            
            return JsonResponse({
                "success": True,
                "message": f"Randomized positions for {len(cars)} cars"
            })
            
        else:
            return JsonResponse({"error": "Unknown action"}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ✅ AJAX UPLOAD SINGLE IMAGE (Individual Processing)
def ajax_upload_single_image(request):
    """AJAX endpoint to upload and process a single image"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)
    
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            car_id = request.POST.get('car_id')
            image_file = request.FILES.get('image')
            
            if not car_id or not image_file:
                return JsonResponse({"success": False, "error": "Car ID and image are required"})
            
            try:
                car = Car.objects.get(id=car_id)
            except Car.DoesNotExist:
                return JsonResponse({"success": False, "error": "Car not found"})
            
            # Get the highest position for existing images and add new one after
            max_position = CarImage.objects.filter(car=car).aggregate(
                max_pos=Max('position')
            )['max_pos'] or 0
            
            # Create CarImage with processing_status as 'pending'
            car_image = CarImage.objects.create(
                car=car,
                image=image_file,
                position=max_position + 1,
                processing_status='pending'
            )
            
            # Start background processing
            thread = threading.Thread(target=process_image_in_background, args=(car_image.id,))
            thread.daemon = True
            thread.start()
            
            return JsonResponse({
                "success": True,
                "image_id": car_image.id,
                "image_url": car_image.image.url if car_image.image else None,
                "position": car_image.position,
                "processing_status": car_image.processing_status,
                "message": "Image uploaded successfully and is being processed"
            })
            
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)


def process_image_in_background(car_image_id):
    """Background function to process image thumbnails and web versions"""
    try:
        car_image = CarImage.objects.get(id=car_image_id)
        car_image.processing_status = 'processing'
        car_image.save()
        
        # ImageKit will automatically generate the thumbnails and web versions
        # when accessed for the first time. We just need to trigger generation.
        # This forces the creation of thumbnail and web_display versions
        if car_image.thumbnail:
            car_image.thumbnail.url  # This triggers generation
        if car_image.web_display:
            car_image.web_display.url  # This triggers generation
            
        car_image.processing_status = 'completed'
        car_image.save()
        
    except CarImage.DoesNotExist:
        pass
    except Exception as e:
        try:
            car_image = CarImage.objects.get(id=car_image_id)
            car_image.processing_status = 'error'
            car_image.save()
        except:
            pass


# ✅ AJAX CHECK IMAGE PROCESSING STATUS
def ajax_check_image_status(request, image_id):
    """Check the processing status of an uploaded image"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)
    
    try:
        car_image = CarImage.objects.get(id=image_id)
        
        # Try to generate thumbnail URL if processing is complete
        thumbnail_url = None
        web_display_url = None
        
        if car_image.processing_status == 'completed':
            try:
                thumbnail_url = car_image.thumbnail.url if car_image.thumbnail else None
                web_display_url = car_image.web_display.url if car_image.web_display else None
            except:
                # If there's an error accessing the generated images, mark as error
                car_image.processing_status = 'error'
                car_image.save()
        
        return JsonResponse({
            "success": True,
            "processing_status": car_image.processing_status,
            "thumbnail_url": thumbnail_url,
            "web_display_url": web_display_url,
            "original_url": car_image.image.url if car_image.image else None
        })
        
    except CarImage.DoesNotExist:
        return JsonResponse({"success": False, "error": "Image not found"})

@login_required
def exclusive_car_management(request):
    """
    Dashboard view for managing exclusive car selection
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/admin/login/?next=/dashboard/cars/exclusive/')

    if request.method == 'POST':
        car_id = request.POST.get('car_id')
        action = request.POST.get('action')

        if action == 'set_exclusive' and car_id:
            try:
                # First, unset any existing exclusive car
                Car.objects.filter(is_exclusive=True).update(is_exclusive=False)

                # Set the selected car as exclusive
                car = get_object_or_404(Car, id=car_id)
                car.is_exclusive = True
                car.save()

                messages.success(request, f'Возилото "{car.title}" е поставено како ексклузивно.')
            except Exception as e:
                messages.error(request, f'Грешка: {str(e)}')

        elif action == 'remove_exclusive':
            try:
                Car.objects.filter(is_exclusive=True).update(is_exclusive=False)
                messages.success(request, 'Ексклузивното возило е отстрането.')
            except Exception as e:
                messages.error(request, f'Грешка: {str(e)}')

        return redirect('exclusive_car_management')

    # Get current exclusive car
    exclusive_car = Car.objects.filter(is_exclusive=True).first()

    # Get all cars for selection
    search_query = request.GET.get('search', '')
    cars = Car.objects.select_related('brand', 'model_name').order_by('-created_at')

    if search_query:
        cars = cars.filter(
            Q(title__icontains=search_query) |
            Q(brand__name__icontains=search_query) |
            Q(model_name__name__icontains=search_query)
        )

    # Paginate cars
    paginator = Paginator(cars, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'exclusive_car': exclusive_car,
        'cars': page_obj,
        'search_query': search_query,
        'total_cars': cars.count(),
    }

    return render(request, 'admin_custom/exclusive_car_management.html', context)

def redirect_to_dashboard(request, invalid=None):
    """
    Redirect invalid dashboard URLs to the main dashboard
    """
    return redirect('/dashboard/')