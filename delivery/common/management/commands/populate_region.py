from django.core.management.base import BaseCommand
from common.models import Country, State, City

class Command(BaseCommand):
    help = 'Populates database with Indian states (Tamil Nadu, Karnataka) and their cities'

    def handle(self, *args, **kwargs):
        # Create or get India
        india, created = Country.objects.get_or_create(
            code='IN',
            defaults={'name': 'India'}
        )
        self.stdout.write(self.style.SUCCESS(f'Country: {india}'))

        # Tamil Nadu data
        tn, created = State.objects.get_or_create(
            code='TN',
            country=india,
            defaults={'name': 'Tamil Nadu'}
        )
        self.stdout.write(self.style.SUCCESS(f'State: {tn}'))

        # Karnataka data
        ka, created = State.objects.get_or_create(
            code='KA',
            country=india,
            defaults={'name': 'Karnataka'}
        )
        self.stdout.write(self.style.SUCCESS(f'State: {ka}'))

        # Cities for Tamil Nadu
        tn_cities = [
            {'code': 'CH', 'name': 'Chennai'},
            {'code': 'CB', 'name': 'Coimbatore'},
            {'code': 'ERD', 'name': 'Erode'},
            {'code': 'SL', 'name': 'Salem'},
        ]

        for city_data in tn_cities:
            city, created = City.objects.get_or_create(
                code=city_data['code'],
                state=tn,
                defaults={'name': city_data['name']}
            )
            self.stdout.write(self.style.SUCCESS(f'City: {city}'))

        # Cities for Karnataka
        ka_cities = [
            {'code': 'BL', 'name': 'Bengaluru'},
            {'code': 'MY', 'name': 'Mysuru'},
            {'code': 'MA', 'name': 'Mangaluru'},
        ]

        for city_data in ka_cities:
            city, created = City.objects.get_or_create(
                code=city_data['code'],
                state=ka,
                defaults={'name': city_data['name']}
            )
            self.stdout.write(self.style.SUCCESS(f'City: {city}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated Indian states and cities!'))