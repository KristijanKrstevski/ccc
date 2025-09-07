import json
from django.core.management.base import BaseCommand
from dealership_app.models import CarBrand, CarModel


class Command(BaseCommand):
    help = "Load car brands and models from cars.json file"

    def handle(self, *args, **kwargs):
        # Load cars.json file
        try:
            with open('cars.json', 'r', encoding='utf-8') as file:
                cars_data = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ cars.json file not found!"))
            return

        brands_created = 0
        models_created = 0

        for brand_name, models in cars_data.items():
            # Create or get brand
            brand, brand_created_flag = CarBrand.objects.get_or_create(name=brand_name)
            if brand_created_flag:
                brands_created += 1
                self.stdout.write(f"✅ Created brand: {brand_name}")

            # Create models for this brand
            for model_name in models:
                model, model_created_flag = CarModel.objects.get_or_create(
                    brand=brand, 
                    name=model_name
                )
                if model_created_flag:
                    models_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Import completed! Created {brands_created} brands and {models_created} models."
            )
        )