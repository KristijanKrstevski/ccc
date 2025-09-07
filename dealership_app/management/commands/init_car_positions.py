from django.core.management.base import BaseCommand
from dealership_app.models import Car

class Command(BaseCommand):
    help = 'Initialize position values for existing cars'

    def handle(self, *args, **options):
        cars_without_positions = Car.objects.filter(position=0).order_by('-created_at')
        
        if not cars_without_positions.exists():
            self.stdout.write(
                self.style.SUCCESS('All cars already have position values!')
            )
            return
        
        self.stdout.write(f'Found {cars_without_positions.count()} cars without position values.')
        
        cars_to_update = []
        for i, car in enumerate(cars_without_positions):
            car.position = i + 1  # Start positions from 1
            cars_to_update.append(car)
            
        # Bulk update for performance
        Car.objects.bulk_update(cars_to_update, ['position'])
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully initialized positions for {len(cars_to_update)} cars!')
        )