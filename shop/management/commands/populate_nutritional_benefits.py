from django.core.management.base import BaseCommand
from shop.models import NutritionalBenefit


class Command(BaseCommand):
    help = 'Populate nutritional benefits with predefined values'

    def handle(self, *args, **options):
        benefits_data = [
            {'name': 'vb1', 'display_name': 'V-B1', 'description': 'Vitamin B1 (Thiamine) - Essential for energy metabolism'},
            {'name': 'vb2', 'display_name': 'V-B2', 'description': 'Vitamin B2 (Riboflavin) - Important for cellular energy production'},
            {'name': 'vb12', 'display_name': 'V-12', 'description': 'Vitamin B12 - Essential for nerve function and red blood cell formation'},
            {'name': 'vb6', 'display_name': 'V-B6', 'description': 'Vitamin B6 - Important for brain development and function'},
            {'name': 'proteins', 'display_name': 'Proteins', 'description': 'High-quality proteins for muscle building and repair'},
            {'name': 'omega_fatty_acids', 'display_name': 'Omega Fatty Acids', 'description': 'Essential fatty acids for heart and brain health'},
            {'name': 'calcium', 'display_name': 'Calcium', 'description': 'Essential mineral for strong bones and teeth'},
            {'name': 'low_fat_diet', 'display_name': 'Low Fat Diet', 'description': 'Suitable for low-fat dietary requirements'},
            {'name': 'iron_zinc', 'display_name': 'Iron-Zinc', 'description': 'Essential minerals for immune function and blood health'},
        ]

        for benefit_data in benefits_data:
            benefit, created = NutritionalBenefit.objects.get_or_create(
                name=benefit_data['name'],
                defaults={
                    'display_name': benefit_data['display_name'],
                    'description': benefit_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created nutritional benefit: {benefit.display_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Nutritional benefit already exists: {benefit.display_name}')
                )

        self.stdout.write(self.style.SUCCESS('Finished populating nutritional benefits'))
