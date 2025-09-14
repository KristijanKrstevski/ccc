import json
import os
import io
from PIL import Image
from django.db import models
from django.core.files.base import ContentFile
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFit, Thumbnail
from pilkit.processors import Anchor
from pilkit.processors.base import ProcessorPipeline




class CarBrand(models.Model):
    name = models.CharField("Марка", max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarModel(models.Model):
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name="models")
    name = models.CharField("Модел", max_length=100)

    class Meta:
        unique_together = ("brand", "name")
        ordering = ["brand__name", "name"]

    def __str__(self):
        return f"{self.name}"


class CarEquipment(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name



class Car(models.Model):
    brand = models.ForeignKey(CarBrand, on_delete=models.SET_NULL, null=True, blank=True)
    model_name = models.ForeignKey(CarModel, on_delete=models.SET_NULL, null=True, blank=True)

    title = models.CharField("Наслов", max_length=200)
    year = models.PositiveSmallIntegerField("Година на производство")
    description = models.TextField("Опис", blank=True)

    FUEL_CHOICES_EN = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('ethanol', 'Ethanol'),
        ('methane', 'Methane'),
        ('lpg', 'LPG/Petrol'),
        ('hybrid_petrol', 'Hybrid/Petrol'),
        ('hybrid_diesel', 'Hybrid/Diesel'),
    ]
    
    FUEL_CHOICES_MK = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизел'),
        ('electric', 'Електричен'),
        ('ethanol', 'Етанол'),
        ('methane', 'Метан'),
        ('lpg', 'Плин/Бензин'),
        ('hybrid_petrol', 'Хибрид/Бензин'),
        ('hybrid_diesel', 'Хибрид/Дизел'),
    ]
    
    # Default to Macedonian for compatibility
    FUEL_CHOICES = FUEL_CHOICES_MK
    fuel_type = models.CharField("Тип на гориво", max_length=20, choices=FUEL_CHOICES)

    TRANSMISSION_CHOICES_EN = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('other', 'Other'),
    ]
    
    TRANSMISSION_CHOICES_MK = [
        ('manual', 'Рачен'),
        ('automatic', 'Автоматски'),
        ('other', 'Друго'),
    ]
    
    TRANSMISSION_CHOICES = TRANSMISSION_CHOICES_MK
    transmission = models.CharField("Менувач", max_length=20, choices=TRANSMISSION_CHOICES)

    BODY_CHOICES_EN = [
        ('compact', 'Compact Car'),
        ('sedan', 'Sedan'),
        ('hatchback', 'Hatchback'),
        ('wagon', 'Wagon'),
        ('coupe', 'Coupe'),
        ('cabriolet', 'Cabriolet'),
        ('suv', 'SUV'),
        ('minivan', 'Minivan'),
        ('kombe', 'Van'),
        ('pickup', 'Pickup'),
        ('motorcycle', 'Motorcycle'),
    ]
    
    BODY_CHOICES_MK = [
        ('compact', 'Мал автомобил'),
        ('sedan', 'Седан'),
        ('hatchback', 'Хеџбек'),
        ('wagon', 'Караван'),
        ('coupe', 'Купе'),
        ('cabriolet', 'Кабриолет'),
        ('suv', 'Теренско'),
        ('minivan', 'Миниван'),
        ('kombe', 'Комбе'),
        ('pickup', 'Пикап'),
        ('motorcycle', 'Мотор'),
    ]
    
    BODY_CHOICES = BODY_CHOICES_MK
    body_type = models.CharField("Тип на каросерија", max_length=20, choices=BODY_CHOICES)

    REGISTRATION_CHOICES_EN = [
        ('mk', 'Macedonian'),
        ('foreign', 'Foreign'),
        ('none', 'To be registered'),
        ('other', 'Other'),
    ]
    
    REGISTRATION_CHOICES_MK = [
        ('mk', 'Македонска'),
        ('foreign', 'Странска'),
        ('none', 'Останува да се регистрира'),
        ('other', 'Друго'),
    ]
    
    REGISTRATION_CHOICES = REGISTRATION_CHOICES_MK
    registration_type = models.CharField("Регистрација", max_length=20, choices=REGISTRATION_CHOICES)

    engine_capacity = models.PositiveIntegerField("Кубикажа (cm³)", null=True, blank=True)

    kilowatts = models.PositiveIntegerField("Киловати")
    price = models.PositiveIntegerField("Цена (во евра)")
    
    # Banner field - single choice selection
    BANNER_CHOICES = [
        ('', 'Без банер'),
        ('sold', 'SOLD'),
        ('pending', 'PENDING'),
        ('coming_soon', 'COMING SOON'),
    ]
    banner_type = models.CharField("Банер", max_length=20, choices=BANNER_CHOICES, blank=True, default='')

    # Badge fields for the new badge system
    show_registered_badge = models.BooleanField("Регистрирано значка", default=False, help_text="Прикажи зелена значка за регистрирано")
    show_serviced_badge = models.BooleanField("Сервисирано значка", default=False, help_text="Прикажи жолта значка за сервисирано")
    show_promo_badge = models.BooleanField("Промотивна цена значка", default=False, help_text="Прикажи црвена значка за промотивна цена")

    sold = models.BooleanField("Продадено", default=False)  # Keep for backward compatibility
    is_exclusive = models.BooleanField("Ексклузивно возило", default=False, help_text="Само едно возило може да биде ексклузивно во исто време")

    mileage = models.PositiveIntegerField("Километража")
    consumption = models.CharField("Потрошувачка (л/100км)", max_length=10, blank=True, null=True)

    COLOR_CHOICES_EN = [
        ('black', 'Black'),
        ('white', 'White'),
        ('gray', 'Gray'),
        ('red', 'Red'),
        ('green', 'Green'),
        ('blue', 'Blue'),
        ('yellow', 'Yellow'),
        ('orange', 'Orange'),
        ('brown', 'Brown'),
        ('gold', 'Gold'),
        ('purple', 'Purple'),
        ('other', 'Other'),
    ]
    
    COLOR_CHOICES_MK = [
        ('black', 'Црна'),
        ('white', 'Бела'),
        ('gray', 'Сива'),
        ('red', 'Црвена'),
        ('green', 'Зелена'),
        ('blue', 'Сина'),
        ('yellow', 'Жолта'),
        ('orange', 'Портокалова'),
        ('brown', 'Кафеава'),
        ('gold', 'Златна'),
        ('purple', 'Виолетова'),
        ('other', 'Друго'),
    ]
    
    COLOR_CHOICES = COLOR_CHOICES_MK
    color = models.CharField("Боја", max_length=20, choices=COLOR_CHOICES)

    SEATS_CHOICES_EN = [
        ('3', '3 seats'),
        ('5', '5 seats'),
        ('7', '7 seats'),
    ]
    
    SEATS_CHOICES_MK = [
        ('3', '3 седишта'),
        ('5', '5 седишта'),
        ('7', '7 седишта'),
    ]
    
    SEATS_CHOICES = SEATS_CHOICES_MK
    seats = models.CharField("Број на седишта", max_length=2, choices=SEATS_CHOICES)

    equipment = models.ManyToManyField(CarEquipment, blank=True)

    # Main image with ImageKit processing
    main_image = ProcessedImageField(
        upload_to='cars/main_images/original/',
        processors=[ResizeToFit(1200, 800)],  # Reduced max size for better performance
        format='JPEG',
        options={'quality': 85},  # Balanced quality for main image
        verbose_name="Главна слика"
    )
    
    # Main image thumbnail
    main_image_thumbnail = ImageSpecField(
        source='main_image',
        processors=[Thumbnail(250, 250)],
        format='JPEG',
        options={'quality': 75}
    )
    
    # Main image web display version (~500KB target)
    main_image_web = ImageSpecField(
        source='main_image',
        processors=[ResizeToFit(800, 550)],  # Optimized size for main image
        format='JPEG',
        options={'quality': 65, 'progressive': True, 'optimize': True}  # Aggressive compression for 500KB target
    )
    
    # Position field for ordering cars
    position = models.PositiveIntegerField("Позиција", default=0, help_text="Позиција за подредување на возилата")

    created_at = models.DateTimeField("Креирано", auto_now_add=True)

    @classmethod
    def get_fuel_choices(cls, language='mk'):
        """Return fuel choices based on language"""
        return cls.FUEL_CHOICES_EN if language == 'en' else cls.FUEL_CHOICES_MK
    
    @classmethod
    def get_transmission_choices(cls, language='mk'):
        """Return transmission choices based on language"""
        return cls.TRANSMISSION_CHOICES_EN if language == 'en' else cls.TRANSMISSION_CHOICES_MK
    
    @classmethod
    def get_body_choices(cls, language='mk'):
        """Return body choices based on language"""
        return cls.BODY_CHOICES_EN if language == 'en' else cls.BODY_CHOICES_MK
    
    @classmethod
    def get_registration_choices(cls, language='mk'):
        """Return registration choices based on language"""
        return cls.REGISTRATION_CHOICES_EN if language == 'en' else cls.REGISTRATION_CHOICES_MK
    
    @classmethod
    def get_color_choices(cls, language='mk'):
        """Return color choices based on language"""
        return cls.COLOR_CHOICES_EN if language == 'en' else cls.COLOR_CHOICES_MK
    
    @classmethod
    def get_seats_choices(cls, language='mk'):
        """Return seats choices based on language"""
        return cls.SEATS_CHOICES_EN if language == 'en' else cls.SEATS_CHOICES_MK

    def get_fuel_type_display_lang(self, language='mk'):
        """Return fuel type display value based on language"""
        choices_dict = dict(self.get_fuel_choices(language))
        return choices_dict.get(self.fuel_type, self.fuel_type)
    
    def get_transmission_display_lang(self, language='mk'):
        """Return transmission display value based on language"""
        choices_dict = dict(self.get_transmission_choices(language))
        return choices_dict.get(self.transmission, self.transmission)
    
    def get_body_type_display_lang(self, language='mk'):
        """Return body type display value based on language"""
        choices_dict = dict(self.get_body_choices(language))
        return choices_dict.get(self.body_type, self.body_type)
    
    def get_registration_type_display_lang(self, language='mk'):
        """Return registration type display value based on language"""
        choices_dict = dict(self.get_registration_choices(language))
        return choices_dict.get(self.registration_type, self.registration_type)
    
    def get_color_display_lang(self, language='mk'):
        """Return color display value based on language"""
        choices_dict = dict(self.get_color_choices(language))
        return choices_dict.get(self.color, self.color)
    
    def get_seats_display_lang(self, language='mk'):
        """Return seats display value based on language"""
        choices_dict = dict(self.get_seats_choices(language))
        return choices_dict.get(self.seats, self.seats)

    def get_registered_badge_text(self, language='mk'):
        """Return registered badge text based on language"""
        return "Registered" if language == 'en' else "Регистрирано"

    def get_serviced_badge_text(self, language='mk'):
        """Return serviced badge text based on language"""
        return "Serviced" if language == 'en' else "Сервисирано"

    def get_promo_badge_text(self, language='mk'):
        """Return promo badge text based on language"""
        return "Promo Price" if language == 'en' else "Промо цена"

    class Meta:
        ordering = ['position', '-created_at']
        verbose_name = "Автомобил"
        verbose_name_plural = "Автомобили"

    def display_price(self):
        return "По договор" if self.price == 0 else f"{self.price:,} €"

    def get_extra_images_list(self):
        """Return URLs of all extra images for this car"""
        return [img.image.url for img in self.images.all() if img.image]
    
    def delete(self, *args, **kwargs):
        """Override delete to remove image files from filesystem"""
        import os
        
        # Delete extra images
        for img in self.images.all():
            if img.image and os.path.isfile(img.image.path):
                os.remove(img.image.path)
        
        # Delete main image
        if self.main_image and os.path.isfile(self.main_image.path):
            os.remove(self.main_image.path)
        
        # Call the parent delete method
        super().delete(*args, **kwargs)

    @property
    def horsepower(self):
        """Calculate horsepower from kilowatts: kW × 1.36 and round up"""
        if self.kilowatts:
            import math
            return math.ceil(self.kilowatts * 1.36)
        return None

    def get_mileage_display(self):
        """Display mileage with proper formatting"""
        if self.mileage:
            return f"{self.mileage:,} км"
        return "0 км"


    def get_total_size(self):
        """Calculate total size of car (main image + extra images)"""
        total_size = 0
        
        # Add main image size
        if self.main_image:
            total_size += self.main_image.size
            
        # Add extra images sizes
        for img in self.images.all():
            if img.image:
                total_size += img.image.size
                
        return total_size
    
    def clean(self):
        """Validate that total car size doesn't exceed 5MB"""
        from django.core.exceptions import ValidationError
        
        # Skip size validation for new instances (no pk yet)
        if not self.pk:
            return
            
        max_total_size = 5 * 1024 * 1024  # 5MB in bytes
        total_size = self.get_total_size()
        
        if total_size > max_total_size:
            raise ValidationError(
                f'Total car size ({total_size / (1024*1024):.1f}MB) exceeds 5MB limit. '
                f'Please use fewer or smaller images.'
            )

    def save(self, *args, **kwargs):
        """Override save method - ImageKit handles compression automatically"""
        # Run validation
        self.clean()

        # If this car is being marked as exclusive, unmark any other exclusive cars
        if self.is_exclusive:
            Car.objects.exclude(pk=self.pk).update(is_exclusive=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="images")
    
    # Original image - will be processed automatically by ImageKit
    image = ProcessedImageField(
        upload_to='cars/extra_images/original/',
        processors=[ResizeToFit(1200, 800)],  # Reduced max size for better compression
        format='JPEG',
        options={'quality': 85}
    )
    
    # Thumbnail version (150x150) - smaller for faster loading
    thumbnail = ImageSpecField(
        source='image',
        processors=[Thumbnail(150, 150)],
        format='JPEG',
        options={'quality': 70}
    )
    
    # Web display version (700x500 max, ~500KB target)
    web_display = ImageSpecField(
        source='image',
        processors=[ResizeToFit(700, 500)],
        format='JPEG',
        options={'quality': 60, 'progressive': True, 'optimize': True}  # Aggressive compression for 500KB target
    )
    
    position = models.PositiveIntegerField("Position", default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    processing_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('error', 'Error')
        ],
        default='pending'
    )

    class Meta:
        ordering = ['position', 'id']

    def delete(self, *args, **kwargs):
        """Override delete to remove image files from filesystem"""
        import os
        
        # Delete the original image file
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
            
        # Delete generated thumbnails and web display versions if they exist
        try:
            if self.thumbnail and os.path.isfile(self.thumbnail.path):
                os.remove(self.thumbnail.path)
        except:
            pass
            
        try:
            if self.web_display and os.path.isfile(self.web_display.path):
                os.remove(self.web_display.path)
        except:
            pass
        
        # Call the parent delete method
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.car.title}"
