# orders viws.py
import json
import datetime

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.http import Http404, JsonResponse
from django.contrib import messages
import razorpay
from django.conf import settings
from cart.models import CartItem, Cart
from cart.views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from .forms import OrderForm
from .models import Order, Payment, OrderProduct, TimingSlot, CODPayment
from shop.models import Product
from django.core.mail import send_mail
from django.utils.html import strip_tags



@login_required(login_url = 'accounts:login')
def payment_method(request):
    return render(request, 'shop/orders/payment_method.html',)


@login_required(login_url = 'accounts:login')
def checkout(request,total=0, total_price=0, quantity=0, cart_items=None):
    tax = 0.00
    handing = 0.00
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total_price += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        total = total_price + 10

    except ObjectDoesNotExist:
        pass # just ignore

    
    tax = round(((2 * total_price)/100), 2)
    grand_total = total_price #+ tax
    # handing = 15.00
    total = float(grand_total) #+ handing
    
    context = {
        'total_price': total_price,
        'quantity': quantity,
        'cart_items':cart_items,
        'handing': handing,
        'vat' : tax,
        'order_total': total,
    }
    return render(request, 'shop/orders/checkout/checkout.html', context)




from .models import Payment

@login_required(login_url='accounts:login')
def payment(request, total=0, quantity=0):
    current_user = request.user
    handing = 15.0
    # if the cart count less than 0, redirect to shop page
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop:shop')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = round(((2 * total) / 100), 2)

    grand_total = total #+ tax
    # handing = 15.00
    total = float(grand_total) #+ handing

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Save all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.payment_method = 'Cash On Delivery'  # Mark payment method as COD
            data.status = 'New'  # Set order status to New
            timing_slot_id = request.POST.get('timing_slot')
            if timing_slot_id:
                try:
                    timing_slot = TimingSlot.objects.get(slot=timing_slot_id)
                except TimingSlot.DoesNotExist:
                    raise Http404("Timing slot not found")
                data.timing_slot = timing_slot
                data.save()
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")  # 20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            cart_items = CartItem.objects.filter(user=current_user)
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order = data
                order_product.user = current_user
                order_product.product = item.product
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

                # add variation to OrderProduct table
                cart_item = CartItem.objects.get(id=item.id)
                product_variation = cart_item.variation.all()
                order_product = OrderProduct.objects.get(id=order_product.id)
                order_product.variations.set(product_variation)
                order_product.save()

                # Reduce the quantity of sold products
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()
                

            # Clear Cart
            CartItem.objects.filter(user=current_user).delete()
            
            return redirect('orders:order_completed')
        else:
            messages.error(request, 'Your information is not valid')
            return redirect('orders:checkout')
    else:
        return redirect('shop:shop')








razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required(login_url='accounts:login')
def payment(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop:shop')

    # Calculate totals
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = round(((2 * total) / 100), 2)
    grand_total = total

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Create order
            order = Order()
            order.user = current_user
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone = form.cleaned_data['phone']
            order.email = form.cleaned_data['email']
            order.address = form.cleaned_data['address']
            order.order_note = form.cleaned_data['order_note']
            order.order_total = grand_total
            order.tax = tax
            order.ip = request.META.get('REMOTE_ADDR')
            
            # Handle timing slot
            timing_slot_id = request.POST.get('timing_slot')
            if timing_slot_id:
                try:
                    timing_slot = TimingSlot.objects.get(slot=timing_slot_id)
                    order.timing_slot = timing_slot
                except TimingSlot.DoesNotExist:
                    raise Http404("Timing slot not found")
            
            order.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(order.id)
            order.order_number = order_number
            order.save()

            # Create Razorpay order
            razorpay_order_amount = int(grand_total * 100)  # Convert to paisa
            razorpay_order = razorpay_client.order.create({
                'amount': razorpay_order_amount,
                'currency': 'INR',
                'payment_capture': '1'
            })

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                'razorpay_amount': razorpay_order_amount,
                'callback_url': 'http://' + request.get_host() + '/orders/payment/verify/'
            }
            return render(request, 'shop/orders/checkout/payment.html', context)
    
    return redirect('orders:checkout')

@login_required(login_url='accounts:login')
def payment_verify(request):
    if request.method == 'POST':
        try:
            payment_data = json.loads(request.body)
            razorpay_order_id = payment_data.get('razorpay_order_id')
            razorpay_payment_id = payment_data.get('razorpay_payment_id')
            razorpay_signature = payment_data.get('razorpay_signature')
            order_number = payment_data.get('orderID')

            # Verify signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
            except:
                return JsonResponse({'error': 'Invalid payment signature'}, status=400)

            # Get the order
            order = Order.objects.get(order_number=order_number, is_ordered=False)

            # Create payment record
            payment = Payment(
                user=request.user,
                payment_id=razorpay_payment_id,
                order_number=order_number,
                payment_method='Razorpay',
                amount_paid=order.order_total,
                payment_status='Completed'
            )
            payment.save()

            # Update order
            order.payment = payment
            order.is_ordered = True
            order.status = 'Accepted'
            order.save()

            # Move cart items to order products
            cart_items = CartItem.objects.filter(user=request.user)
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order = order
                order_product.payment = payment
                order_product.user = request.user
                order_product.product = item.product
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

                # Add variations
                cart_item = CartItem.objects.get(id=item.id)
                product_variation = cart_item.variation.all()
                order_product.variations.set(product_variation)
                order_product.save()

                # Reduce product stock
                product = item.product
                product.stock -= item.quantity
                product.save()

            # Clear cart
            CartItem.objects.filter(user=request.user).delete()

            # Return success response
            response_data = {
                'order_number': order.order_number,
                'transID': payment.payment_id,
                'success': True
            }
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)





@login_required(login_url='accounts:login')
def cod_payment(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop:shop')

    # Calculate totals
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = round(((2 * total) / 100), 2)
    grand_total = total

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                # Create order
                order = Order()
                order.user = current_user
                order.first_name = form.cleaned_data['first_name']
                order.last_name = form.cleaned_data['last_name']
                order.phone = form.cleaned_data['phone']
                order.email = form.cleaned_data['email']
                order.address = form.cleaned_data['address']
                order.order_note = form.cleaned_data['order_note']
                order.order_total = grand_total
                order.tax = tax
                order.ip = request.META.get('REMOTE_ADDR')
                order.payment_method = 'COD'
                order.status = 'New'
                order.is_ordered = True  # Set to True since we're completing the order immediately
                
                # Handle timing slot
                timing_slot_id = request.POST.get('timing_slot')
                if timing_slot_id:
                    timing_slot = TimingSlot.objects.get(slot=timing_slot_id)
                    order.timing_slot = timing_slot
                
                order.save()

                # Generate order number
                yr = int(datetime.date.today().strftime('%Y'))
                dt = int(datetime.date.today().strftime('%d'))
                mt = int(datetime.date.today().strftime('%m'))
                d = datetime.date(yr, mt, dt)
                current_date = d.strftime("%Y%m%d")
                order_number = current_date + str(order.id)
                order.order_number = order_number
                order.save()

                # Create Payment record
                payment = Payment.objects.create(
                    user=current_user,
                    payment_id=f'COD_{order_number}',
                    order_number=order_number,
                    payment_method='COD',
                    amount_paid=str(grand_total),
                    payment_status='Pending'  # Keep as pending since it's COD
                )
                order.payment = payment
                order.save()

                # Move cart items to order products
                for item in cart_items:
                    order_product = OrderProduct.objects.create(
                        order=order,
                        payment=payment,
                        user=current_user,
                        product=item.product,
                        quantity=item.quantity,
                        product_price=item.product.price,
                        ordered=True
                    )

                    # Add variations if any
                    cart_item = CartItem.objects.get(id=item.id)
                    product_variation = cart_item.variation.all()
                    order_product.variations.set(product_variation)

                    # Reduce stock
                    product = item.product
                    product.stock -= item.quantity
                    product.save()

                # Clear cart
                cart_items.delete()

                # Redirect to order completed page with parameters
                param = f'?order_number={order_number}&payment_id={payment.payment_id}'
                return redirect(f'/orders/order_completed/{param}')

            except Exception as e:
                messages.error(request, f'Error processing order: {str(e)}')
                return redirect('orders:checkout')

    return redirect('orders:checkout')



def order_completed(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotall = 0
        for i in ordered_products:
            subtotall += i.product_price * i.quantity
        subtotal = round(subtotall, 2)
        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'shop/orders/order_completed/order_completed.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('shop:shop')
    

