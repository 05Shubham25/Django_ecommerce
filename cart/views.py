#cart views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from decimal import Decimal
from shop.models import Product, Variation

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    
    # Initialize variables
    product_variation = []
    variation_price = 0
    
    # Get quantity from POST data, default to 1
    quantity = int(request.POST.get('quantity', 1))
    
    # Validate stock availability
    if quantity > product.stock:
        return JsonResponse({
            'success': False,
            'message': 'Requested quantity exceeds available stock'
        })

    # Process variations from POST data
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
                # Add ₹25 if marination is selected
                if variation.variation_category.lower() == 'marination' and value:
                    variation_price = 25
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    if current_user.is_authenticated:
        # Handle cart for authenticated users
        try:
            cart_items = CartItem.objects.filter(
                product=product,
                user=current_user
            )
            
            existing_variations = [list(item.variation.all()) for item in cart_items]
            item_ids = [item.id for item in cart_items]
            
            if product_variation in existing_variations:
                # Update existing cart item
                index = existing_variations.index(product_variation)
                item_id = item_ids[index]
                cart_item = CartItem.objects.get(id=item_id)
                cart_item.quantity = quantity  # Set new quantity
                cart_item.save()
            else:
                # Create new cart item
                cart_item = CartItem.objects.create(
                    product=product,
                    user=current_user,
                    quantity=quantity
                )
                if product_variation:
                    cart_item.variation.add(*product_variation)
                cart_item.save()
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error processing cart: {str(e)}'
            })
    else:
        # Handle cart for anonymous users
        try:
            cart = Cart.objects.get_or_create(cart_id=_cart_id(request))[0]
            cart_items = CartItem.objects.filter(
                product=product,
                cart=cart
            )
            
            existing_variations = [list(item.variation.all()) for item in cart_items]
            item_ids = [item.id for item in cart_items]
            
            if product_variation in existing_variations:
                # Update existing cart item
                index = existing_variations.index(product_variation)
                item_id = item_ids[index]
                cart_item = CartItem.objects.get(id=item_id)
                cart_item.quantity = quantity  # Set new quantity
                cart_item.save()
            else:
                # Create new cart item
                cart_item = CartItem.objects.create(
                    product=product,
                    cart=cart,
                    quantity=quantity
                )
                if product_variation:
                    cart_item.variation.add(*product_variation)
                cart_item.save()
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error processing cart: {str(e)}'
            })

    # Calculate updated totals
    try:
        if current_user.is_authenticated:
            cart_items = CartItem.objects.filter(user=current_user)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)
        
        total = Decimal('0.00')
        for item in cart_items:
            item_variation_price = Decimal('25.00') if any(
                var.variation_category.lower() == 'marination' 
                for var in item.variation.all()
            ) else Decimal('0.00')
            total += (item.product.price + item_variation_price) * item.quantity
        
        # Calculate cart total
        cart_total = {
            'subtotal': str(total),
            'tax': str(round((Decimal('0.02') * total), 2)),  # 2% tax
            'grand_total': str(round(total + (Decimal('0.02') * total), 2))
        }
        
        return JsonResponse({
            'success': True,
            'cart_item_id': cart_item.id,
            'quantity': cart_item.quantity,
            'cart_total': cart_total
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error calculating totals: {str(e)}'
        })

def update_cart(request, product_id, cart_item_id):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        })
    
    try:
        quantity = int(request.POST.get('quantity', 0))
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Invalid quantity'
            })
        
        # Get product and validate stock
        product = get_object_or_404(Product, id=product_id)
        if quantity > product.stock:
            return JsonResponse({
                'success': False,
                'message': 'Requested quantity exceeds available stock'
            })
        
        # Get cart item based on authentication
        if request.user.is_authenticated:
            cart_item = get_object_or_404(
                CartItem,
                product=product,
                user=request.user,
                id=cart_item_id
            )
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = get_object_or_404(
                CartItem,
                product=product,
                cart=cart,
                id=cart_item_id
            )
        
        # Update quantity
        cart_item.quantity = quantity
        cart_item.save()
        
        # Calculate item subtotal with variations
        item_variation_price = Decimal('25.00') if any(
            var.variation_category.lower() == 'marination' 
            for var in cart_item.variation.all()
        ) else Decimal('0.00')
        item_subtotal = (cart_item.product.price + item_variation_price) * quantity
        
        # Calculate cart totals
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart)
        
        cart_total = sum(
            (item.product.price + (Decimal('25.00') if any(
                var.variation_category.lower() == 'marination' 
                for var in item.variation.all()
            ) else Decimal('0.00'))) * item.quantity
            for item in cart_items
        )
        
        tax = round((Decimal('0.02') * cart_total), 2)  # 2% tax
        grand_total = cart_total + tax
        
        return JsonResponse({
            'success': True,
            'item_subtotal': str(item_subtotal),
            'cart_total': str(cart_total),
            'tax': str(tax),
            'grand_total': str(grand_total)
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid quantity value'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating cart: {str(e)}'
        })

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
        
        # Calculate total with variation price
        total_price = sum([
            (item.product.price + (25 if any(var.variation_category == 'marination' for var in item.variation.all()) else 0)) * item.quantity 
            for item in cart_items
        ])
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