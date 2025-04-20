from django.db import models
from django.urls import reverse
from accounts.models import Account
from django.db.models import Avg, Count
from django.core.exceptions import ValidationError
from django.contrib import admin


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=250, blank=True)
    image = models.ImageField(upload_to='categories', blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'categories'

    def get_category_slug_url(self):
        return reverse('shop:categries', args=[self.slug])

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=300, blank=True)
    quantity = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    discount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='photos/products')
    stock = models.IntegerField()
    new = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    date_joined_for_format = models.DateTimeField(auto_now_add=True)
    last_login_for_format = models.DateTimeField(auto_now=True)
    def created(self):
        return self.date_joined_for_format.strftime('%B %d %Y')
    def updated(self):
        return self.last_login_for_format.strftime('%B %d %Y')

    def __str__(self):
        return self.name
    
    def averageRating(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg
    
    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

    def get_prodcut_details_url(self):
        return reverse('shop:product_details', args=[self.category.slug, self.slug])
    
    class Meta:
        verbose_name_plural = 'Products'
        ordering = ('-date_joined_for_format',)
    
VARIATION_VALUES = {
    'marination': [
        'Tandoori Masala',
        'Red Masala',
        'Green Masala'
    ],
    'cut': [
        'Cut into Pieces',
        'Cut for Fillings'
    ],
    'cleaning': [
        'Yes',
        'No'
    ]
}

class Variation(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    variation_category = models.CharField(
        max_length=100,
        choices=[
            ('marination', 'Marination'),
            ('cut', 'How to Cut'),
            ('cleaning', 'Cleaned and Deveined')
        ]
    )
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # If this is a new variation (no ID yet)
        if not self.pk and not self.variation_value:
            super().save(*args, **kwargs)
            # Get all predefined values for this category
            values = VARIATION_VALUES.get(self.variation_category, [])
            
            # Create additional variations for all values
            existing_variations = Variation.objects.filter(
                product=self.product,
                variation_category=self.variation_category
            ).values_list('variation_value', flat=True)
            
            for value in values:
                if value not in existing_variations:
                    Variation.objects.create(
                        product=self.product,
                        variation_category=self.variation_category,
                        variation_value=value,
                        is_active=self.is_active
                    )
            
            # Delete this empty variation
            self.delete()
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.get_variation_category_display()} - {self.variation_value}"

  # You'll need to create this JS file


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    # user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True)
    # subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=700, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_at(self):
        return self.updated_at.strftime('%B %d, %Y')

    def hour_update(self):
        return self.updated_at.strftime('%H:%M:%S')

    def __str__(self):
        return self.review


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None ,on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_gallery')
    
    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'

    def __str__(self):
        return self.product.name



class image_slider(models.Model):
    image = models.ImageField(upload_to='static/img/slider')




class product_of_the_day(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    is_featured = models.BooleanField(default=False)
    # image = models.ImageField(upload_to='product_of_the_day')

    def __str__(self):
        return self.product.name