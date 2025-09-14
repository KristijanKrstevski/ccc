from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Car
from .forms import CarModelForm

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    form = CarModelForm

    list_display = ["thumbnail", "title", "brand", "model_name", "year", "display_price", "sold", "is_exclusive"]
    list_filter = ["brand", "fuel_type", "transmission", "body_type", "seats", "sold", "is_exclusive"]
    search_fields = ["brand__name", "model_name__name", "description"]
    filter_horizontal = ["equipment"]
    readonly_fields = ("display_extra_images",)

    fieldsets = (
        ("Основни информации", {
            "fields": ("brand", "model_name", "title", "year", "description")
        }),
        ("Технички детали", {
            "fields": ("fuel_type", "transmission", "body_type", "registration_type",
                       "engine_capacity", "kilowatts", "mileage", "color", "seats")
        }),
        ("Цена и статус", {
            "fields": ("price", "sold", "is_exclusive")
        }),
        ("Слики и опрема", {
            "fields": ("main_image", "display_extra_images", "equipment")
        }),
    )

    def thumbnail(self, obj):
        if obj.main_image:
            return format_html(
                '<img src="{}" style="width:70px; height:auto; border-radius:4px;" />',
                obj.main_image.url
            )
        return "❌ No image"
    thumbnail.short_description = "Главна слика"

    @admin.display(description="Дополнителни слики")
    def display_extra_images(self, obj):
        images = obj.get_extra_images_list()
        if not images:
            return "Нема дополнителни слики"
        return format_html(''.join(
            f'<img src="{url}" style="height:70px; margin-right:5px; border-radius:4px;" />'
            for url in images
        ))
