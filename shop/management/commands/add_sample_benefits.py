from django.core.management.base import BaseCommand
from shop.models import Product, NutritionalBenefit
import random


class Command(BaseCommand):
    help = 'Add sample nutritional benefits to existing products for testing'

    def handle(self, *args, **options):
        products = Product.objects.all()
        benefits = list(NutritionalBenefit.objects.all())
        
        if not benefits:
            self.stdout.write(
                self.style.ERROR('No nutritional benefits found. Please run populate_nutritional_benefits first.')
            )
            return
        
        for product in products:
            # Randomly assign 2-4 benefits to each product
            num_benefits = random.randint(2, 4)
            selected_benefits = random.sample(benefits, min(num_benefits, len(benefits)))
            
            product.nutritional_benefits.set(selected_benefits)
            
            benefit_names = [benefit.display_name for benefit in selected_benefits]
            self.stdout.write(
                self.style.SUCCESS(f'Added benefits to {product.name}: {", ".join(benefit_names)}')
            )
        
        self.stdout.write(self.style.SUCCESS('Finished adding sample nutritional benefits to products'))
