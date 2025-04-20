from django.contrib import admin
from .models import Category, Product, Variation, ReviewRating, ProductGallery, image_slider, product_of_the_day
import admin_thumbnails

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price','new', 'discount', 'stock', 'created', 'updated', 'is_available']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_available', 'category', 'new']
    list_editable = ['price','discount', 'is_available', 'stock', 'new']
    readonly_fields = ['created', 'updated', ]
    inlines = [ProductGalleryInline]

@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_filter = ('variation_category', 'is_active', 'product')
    list_editable = ('is_active',)
    search_fields = ('product__name',)
    
    # Only show product and variation_category in the add form
    def get_fields(self, request, obj=None):
        if obj is None:  # This is the add form
            return ('product', 'variation_category')
        # This is the change form
        return ('product', 'variation_category', 'variation_value', 'is_active')

    def save_model(self, request, obj, form, change):
        if not change:  # Only for new variations
            obj.save()  # This will trigger our custom save method
        else:
            super().save_model(request, obj, form, change)

admin.site.register(ReviewRating)


@admin.register(ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    list_filter = ['product']


admin.site.register(image_slider)

@admin.register(product_of_the_day)
class product_of_the_dayAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_featured')
    list_filter = ('is_featured',)
    search_fields = ('product__name',)
