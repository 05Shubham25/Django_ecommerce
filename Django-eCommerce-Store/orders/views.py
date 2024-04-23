
import json
import datetime

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
# from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.contrib import messages
import razorpay

from cart.models import CartItem, Cart
from cart.views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
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


# @login_required(login_url='accounts:login')
# def payment(request, total=0, quantity=0):
#     current_user = request.user
#     handing = 15.0
#     # if the cart count less than 0, redirect to shop page
#     cart_items = CartItem.objects.filter(user=current_user)
#     cart_count = cart_items.count()
#     if cart_count <= 0:
#         return redirect('shop:shop')

#     grand_total = 0
#     tax = 0
#     for cart_item in cart_items:
#         total += (cart_item.product.price * cart_item.quantity)
#         quantity += cart_item.quantity
#     tax = round(((2 * total) / 100), 2)

#     grand_total = total #+ tax
#     # handing = 15.00
#     total = float(grand_total) #+ handing

#     if request.method == 'POST':
#         form = OrderForm(request.POST)
#         amount = int(total) * 100  # Amount in paisa
#         order_currency = 'INR'
#         client = razorpay.Client(auth=('rzp_test_fiZWppjz3NNDPW', 'knbW0AEQs9HQmeGk7dreVktl'))
#         payment = client.order.create({'amount': amount, 'currency': order_currency, 'payment_capture': 1})
#         # print(payment)
#         razor_pay_id = payment['id']
#         # print(razor_pay_id)
#         if form.is_valid():
#             # Save all the billing information inside Order table
#             data = Order()
#             data.user = current_user
#             data.first_name = form.cleaned_data['first_name']
#             data.last_name = form.cleaned_data['last_name']
#             data.phone = form.cleaned_data['phone']
#             data.email = form.cleaned_data['email']
#             data.address = form.cleaned_data['address']
#             data.order_note = form.cleaned_data['order_note']
#             data.order_total = total
#             data.tax = tax
#             data.ip = request.META.get('REMOTE_ADDR')
#             # data.razor_pay_id = razor_pay_id
#             data.save()
#             # Generate order number
#             current_date = datetime.date.today().strftime("%Y%m%d")  # 20210305
#             order_number = f"{current_date}{data.id}"
#             data.order_number = order_number
#             data.save()

#             order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
#             context = {
#                 'order': order,
#                 'cart_items': cart_items,
#                 'handing': handing,
#                 'vat': tax,
#                 'order_total': total,
#                 'payment': payment,
#                 'razor_pay_id': razor_pay_id 
                
#             }
#             return render(request, 'shop/orders/checkout/payment.html', context )
#         else:
#             messages.error(request, 'Your information is not valid')
#             return redirect('orders:checkout')

#     else:
#         return redirect('shop:shop')



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








# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=('rzp_test_fiZWppjz3NNDPW', 'knbW0AEQs9HQmeGk7dreVktl'))

def payments(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

        # Calculate amount in paisa
        amount = int(order.order_total * 100)  # Amount in paisa
        order_currency = 'INR'

        # Create Razorpay order
        payment = razorpay_client.order.create({'amount': amount, 'currency': order_currency, 'payment_capture': 1})
        TransID = payment['id']
        print(payment)

        # Store transaction details inside Payment model
        payment_obj = Payment(
            user=request.user,
            payment_id=TransID,
            payment_method=body['payment_method'],
            status=body['status'],
            amount_paid=order.order_total,
        )
        payment_obj.save()

        order.payment = payment_obj
        order.is_ordered = True
        order.save()

        #  Move the cart item to OrderProduct table 
        cart_items = CartItem.objects.filter(user=request.user)
        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()
            
            # add variation to OrderProduct table
            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variation.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()

            
            # Reduce the quantity of the sold products
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

        # Clear Cart 
        CartItem.objects.filter(user=request.user).delete()
        data = {
            'order_number': order.order_number,
            'transID': payment_obj.payment_id,
        }
        return JsonResponse(data)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)




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
    


