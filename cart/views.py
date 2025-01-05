#cart views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from shop.models import Product, Variation

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)  # Get the product
    product_variation = []

    # Handle product variations from POST request
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    if current_user.is_authenticated:
        # User is authenticated, link cart items to user
        cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            existing_variations = [list(item.variation.all()) for item in cart_item]
            item_ids = [item.id for item in cart_item]

            if product_variation in existing_variations:
                index = existing_variations.index(product_variation)
                item_id = item_ids[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    user=current_user
                )
                if product_variation:
                    item.variation.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user
            )
            if product_variation:
                cart_item.variation.add(*product_variation)
            cart_item.save()
    else:
        # User is not authenticated, use session-based cart
        cart = Cart.objects.get_or_create(cart_id=_cart_id(request))[0]
        cart.save()
        cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            existing_variations = [list(item.variation.all()) for item in cart_item]
            item_ids = [item.id for item in cart_item]

            if product_variation in existing_variations:
                index = existing_variations.index(product_variation)
                item_id = item_ids[index]
                item = CartItem.objects.get(id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(
                    product=product,
                    quantity=1,
                    cart=cart
                )
                if product_variation:
                    item.variation.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart
            )
            if product_variation:
                cart_item.variation.add(*product_variation)
            cart_item.save()

    # Return JSON response for AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_items = CartItem.objects.filter(user=current_user) if current_user.is_authenticated else CartItem.objects.filter(cart=cart)
        total = sum([item.product.price * item.quantity for item in cart_items])
        quantity = sum([item.quantity for item in cart_items])

        return JsonResponse({
            'quantity': quantity,
            'total': total,
            'success': True,
        })

    return redirect('cart:cart')

def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

        # Calculate updated totals for AJAX response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            
            total_price = sum(item.product.price * item.quantity for item in cart_items)
            tax = round(((2 * total_price)/100), 2)
            grand_total = total_price

            return JsonResponse({
                'success': True,
                'quantity': cart_item.quantity,
                'sub_total': cart_item.product.price * cart_item.quantity,
                'total': total_price,
                'order_total': grand_total
            })

    except:
        pass

    return redirect('cart:cart')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        
        cart_item.delete()

        # Calculate updated totals for AJAX response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            
            total_price = sum(item.product.price * item.quantity for item in cart_items)
            tax = round(((2 * total_price)/100), 2)
            grand_total = total_price

            return JsonResponse({
                'success': True,
                'total': total_price,
                'order_total': grand_total
            })

    except:
        pass

    return redirect('cart:cart')

def cart(request, total_price=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        quantity = sum(item.quantity for item in cart_items)
    
    except ObjectDoesNotExist:
        pass
    
    tax = round(((2 * total_price)/100), 2)
    grand_total = total_price

    context = {
        'total': total_price,
        'quantity': quantity,
        'cart_items': cart_items,
        'order_total': grand_total,
        'vat': tax,
    }

    return render(request, 'shop/cart/cart.html', context)