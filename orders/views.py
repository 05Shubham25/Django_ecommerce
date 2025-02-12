# orders viws.py
from decimal import Decimal
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
from django.core.mail import EmailMessage
from django.conf import settings


def send_order_email(order, ordered_products):
    """
    Send HTML email with order confirmation to admin
    """
    try:
        subject = f'New Order Received - Order #{order.order_number}'
        
        # Calculate order details
        subtotal = Decimal('0.00')
        marination_tax = Decimal('0.00')
        
        for item in ordered_products:
            subtotal += Decimal(str(item.product_price)) * item.quantity  # Convert product_price to Decimal
            if item.variations.filter(variation_category='marination').exists():
                 marination_tax += Decimal('25.00') * item.quantity  # Keep tax as Decimal
                
        grand_total = subtotal + marination_tax
        
        # Create product rows HTML
        product_rows_html = ""
        for item in ordered_products:
            variations = ", ".join([f"{v.variation_category}: {v.variation_value}" 
                                  for v in item.variations.all()])
            
            image_url = item.product.image.url if item.product.image else ''
            
            product_rows_html += f"""
                <tr>
                    <td>{item.product}</td>
                    <td><img src="{image_url}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 5px;" alt="{item.product}"></td>
                    <td>{variations if variations else 'None'}</td>
                    <td>{item.quantity}</td>
                    <td>₹{item.product_price}</td>
                    <td>₹{item.product_price * item.quantity}</td>
                </tr>
            """

        # Create the email HTML content with inline styles
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto;">
            <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
                <h1>New Order Received!</h1>
                <p>Order #{order.order_number}</p>
            </div>
            
            <div style="padding: 20px;">
                <div style="background-color: #f9f9f9; border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px;">
                    <h2>Order Details</h2>
                    <p><strong>Order Number:</strong> {order.order_number}</p>
                    <p><strong>Date:</strong> {order.created_at.strftime("%B %d, %Y, %I:%M %p")}</p>
                    <p><strong>Payment Method:</strong> {order.payment.payment_method}</p>
                    <p><strong>Payment Status:</strong> <span style="background-color: #4CAF50; color: white; padding: 5px 10px; border-radius: 3px; font-size: 14px;">{order.payment.payment_status}</span></p>
                </div>

                <div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px;">
                    <h2>Customer Information</h2>
                    <p><strong>Name:</strong> {order.first_name} {order.last_name}</p>
                    <p><strong>Email:</strong> {order.email}</p>
                    <p><strong>Phone:</strong> {order.phone}</p>
                    <p><strong>Address:</strong> {order.address}</p>
                </div>

                <h2>Order Items</h2>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #4CAF50; color: white;">Product</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #4CAF50; color: white;">Image</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #4CAF50; color: white;">Variations</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #4CAF50; color: white;">Quantity</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #4CAF50; color: white;">Price</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left; background-color: #4CAF50; color: white;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {product_rows_html}
                    </tbody>
                </table>

                <div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
                    <h2>Order Summary</h2>
                    <p><strong>Subtotal:</strong> ₹{subtotal}</p>
                    <p><strong>Marination Tax:</strong> ₹{marination_tax}</p>
                    <p><strong>Grand Total:</strong> ₹{grand_total:.2f}</p>
                    <p><strong>Delivery Time Slot:</strong> {order.timing_slot if order.timing_slot else 'Not specified'}</p>
                    <p><strong>Order Notes:</strong> {order.order_note if order.order_note else 'None'}</p>
                </div>
            </div>

            <div style="text-align: center; padding: 20px; background-color: #f5f5f5; margin-top: 20px;">
                <p>This is an automated email notification for order #{order.order_number}</p>
            </div>
        </body>
        </html>
        """

        # Create and send email
        email = EmailMessage(
            subject,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
        
    except Exception as e:
        print(f"Failed to send admin email notification: {str(e)}")
        # Re-raise with more context
        raise Exception(f"Email processing error: {str(e)}")



@login_required(login_url = 'accounts:login')
def payment_method(request):
    return render(request, 'shop/orders/payment_method.html',)


@login_required(login_url = 'accounts:login')
def checkout(request,total=0, total_price=0, quantity=0, cart_items=None):
    tax = Decimal('0.00')
    marination_tax = Decimal('0.00')
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total_price += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
            marination_variations = cart_item.variation.filter(variation_category='marination')
            if marination_variations.exists():
                marination_tax += Decimal('25.00') * cart_item.quantity

        total = total_price + 10

    except ObjectDoesNotExist:
        pass # just ignore

    
    tax = round(((2 * total_price)/100), 2)
    grand_total = total_price + marination_tax
    # handing = 15.00
    total = float(grand_total) #+ handing
    
    context = {
        'total_price': total_price,
        'quantity': quantity,
        'cart_items':cart_items,
        'marination_tax': marination_tax,
        'vat' : tax,
        'order_total': total,
    }
    return render(request, 'shop/orders/checkout/checkout.html', context)




from .models import Payment

@login_required(login_url='accounts:login')
def payment(request, total=0, quantity=0):
    current_user = request.user

    # if the cart count less than 0, redirect to shop page
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop:shop')

    grand_total = Decimal('0.00')
    tax = Decimal('0.00')
    marination_tax = Decimal('0.00')
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
        marination_variations = cart_item.variation.filter(variation_category='marination')
        if marination_variations.exists():
            marination_tax += Decimal('25.00') * cart_item.quantity
    tax = round(((2 * total) / 100), 2)

    grand_total = total + marination_tax #+ tax
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
        if cart_item.variation.filter(variation_category='marination').exists():
            marination_tax += Decimal('25.00') * cart_item.quantity 
    grand_total = total + marination_tax

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

            # Send email notification to admin
            ordered_products = OrderProduct.objects.filter(order_id=order.id)
            send_order_email(order, ordered_products)

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
                order.is_ordered = True
                
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
                    payment_status='Pending'
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

                    # Add variations
                    cart_item = CartItem.objects.get(id=item.id)
                    product_variation = cart_item.variation.all()
                    order_product.variations.set(product_variation)

                    # Reduce stock
                    product = item.product
                    product.stock -= item.quantity
                    product.save()

                # Clear cart
                cart_items.delete()

                # Send email notification to admin
                ordered_products = OrderProduct.objects.filter(order_id=order.id)
                send_order_email(order, ordered_products)

                # Redirect to order completed page
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

        # Calculate subtotal
        subtotal = Decimal('0.00')
        marination_tax = Decimal('0.00')
        
        for item in ordered_products:
            # Convert product_price and quantity to Decimal
            price = Decimal(str(item.product_price))
            quantity = Decimal(str(item.quantity))
            subtotal += price * quantity
            print(subtotal)


            
            # Check for marination variations
            if item.variations.filter(variation_category='marination').exists():
                marination_tax += Decimal('25.00') * quantity
                print(marination_tax)

        # Calculate tax
        # tax = round((Decimal('0.02') * subtotal), 2)
        
        # Calculate grand total
        grand_total = subtotal + marination_tax
        print(grand_total)

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
            'marination_tax': marination_tax,
            'grand_total': grand_total,
        }
        return render(request, 'shop/orders/order_completed/order_completed.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('shop:shop')
    

