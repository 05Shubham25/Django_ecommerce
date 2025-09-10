from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import Product, Category, image_slider, Variation, product_of_the_day, NutritionalBenefit, FeatureCategory
from cart.views import _cart_id
from cart.models import CartItem
from .models import ReviewRating
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from .models import ProductGallery
# import razorpay

def home(request):
    products = Product.objects.all().filter(is_available=True)
    
    # First try to get featured products
    featured_products = product_of_the_day.objects.filter(is_featured=True)
    
    # If no featured products are found, get the latest products instead
    if not featured_products.exists():
        # Get latest available products
        latest_products = Product.objects.filter(is_available=True).order_by('-date_joined_for_format')[:6]
        
        # Create temporary product_of_the_day objects for display
        temp_featured = []
        for product in latest_products:
            # Create a simple object with the same structure as product_of_the_day
            temp_featured.append(type('obj', (object,), {
                'product': product,
                'is_featured': True
            }))
        featured_products = temp_featured
    
    # Debug print to check if we have products
    print(f"Featured products count: {len(featured_products)}")
    for item in featured_products:
        print(f"Product: {item.product.name}, Price: {item.product.price}")
    
    context = {
        'products': products,
        'image_slider': image_slider.objects.all(),
        'featured_products': featured_products,
    }
    return render(request, 'shop/index.html', context)


def shop(request, category_slug=None):
    categories = None
    products = None
    
    # Get all nutritional benefits for the filter
    nutritional_benefits = NutritionalBenefit.objects.filter(is_active=True).order_by('display_name')
    
    # Get selected nutritional benefits from request
    selected_benefits = request.GET.getlist('benefits')

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
    else:
        products = Product.objects.all().filter(is_available=True)
    
    # Filter by nutritional benefits if any are selected
    if selected_benefits:
        products = products.filter(nutritional_benefits__name__in=selected_benefits).distinct()
    
    # Pagination
    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    products_count = products.count()
        
    for product in products:
        reviews = ReviewRating.objects.order_by('-updated_at').filter(product_id=product.id, status=True)

    context = {
        'category_slug': category_slug,
        'products': paged_products,
        'products_count': products_count,
        'nutritional_benefits': nutritional_benefits,
        'selected_benefits': selected_benefits,
        'categories': Category.objects.all(),  # Add categories for the dropdown
    }
    return render(request, 'shop/shop/shop.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib import messages

def product_details(request, category_slug, product_details_slug):
    try:
        # Get the product or raise 404
        single_product = get_object_or_404(
            Product, 
            category__slug=category_slug, 
            slug=product_details_slug
        )
        
        # Check if product is in cart
        in_cart = CartItem.objects.filter(
            cart__cart_id=_cart_id(request), 
            product=single_product
        ).exists()
        
        # Get variations by category
        marination_variations = Variation.objects.filter(
            product=single_product,
            variation_category='marination',
            is_active=True
        )
        cut_variations = Variation.objects.filter(
            product=single_product,
            variation_category='cut',
            is_active=True
        )
        cleaning_variations = Variation.objects.filter(
            product=single_product,
            variation_category='cleaning',
            is_active=True
        )
        
        # Check for order product if user is authenticated
        if request.user.is_authenticated:
            orderproduct = OrderProduct.objects.filter(
                user=request.user, 
                product_id=single_product.id
            ).exists()
        else:
            orderproduct = None

        # Get reviews and product gallery
        reviews = ReviewRating.objects.filter(
            product_id=single_product.id, 
            status=True
        ).order_by('-updated_at')
        
        product_gallery = ProductGallery.objects.filter(
            product_id=single_product.id
        )

        context = {
            'single_product': single_product,
            'in_cart': in_cart,
            'orderproduct': orderproduct,
            'reviews': reviews,
            'product_gallery': product_gallery,
            'marination_variations': marination_variations,
            'cut_variations': cut_variations,
            'cleaning_variations': cleaning_variations,
        }
        
        return render(request, 'shop/shop/product_details.html', context)
            
    except Http404:
        messages.error(request, 'Product not found.')
        return redirect('shop:shop')
    except Exception as e:
        messages.error(request, f'An error occurred while loading the product: {str(e)}')
        return redirect('shop:shop')


def search(request):
    products_count = 0
    products = None
    paged_products = None
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword :
            products = Product.objects.filter(Q(description__icontains=keyword) | Q(name__icontains=keyword))
            
            products_count = products.count()
            
    
    context = {
        'products': products,
        'products_count': products_count,
    }
    return render(request, 'shop/shop/search.html', context)


def feature_category(request, feature_slug):
    """View to display products filtered by feature category"""
    try:
        # Get the feature category
        feature_category = get_object_or_404(FeatureCategory, name=feature_slug, is_active=True)
        
        # Get products for this feature category
        products = Product.objects.filter(feature_category=feature_category, is_available=True)
        
        # Get all nutritional benefits for the filter
        nutritional_benefits = NutritionalBenefit.objects.filter(is_active=True).order_by('display_name')
        
        # Get selected nutritional benefits from request
        selected_benefits = request.GET.getlist('benefits')
        
        # Filter by nutritional benefits if any are selected
        if selected_benefits:
            products = products.filter(nutritional_benefits__name__in=selected_benefits).distinct()
        
        # Pagination
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        products_count = products.count()
        
        context = {
            'feature_category': feature_category,
            'products': paged_products,
            'products_count': products_count,
            'nutritional_benefits': nutritional_benefits,
            'selected_benefits': selected_benefits,
            'categories': Category.objects.all(),
        }
        return render(request, 'shop/shop/feature_category.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading products: {str(e)}')
        return redirect('shop:shop')



def review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id,product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you, your review updated!')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you, your review Posted!')
                return redirect(url)
