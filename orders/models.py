from django.db import models
from accounts.models import Account
from shop.models import Product, Variation 
import random
import string

class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    order_number = models.CharField(max_length=20, blank=True)
    PAYMENT_METHODS = (
        ('Razorpay', 'Razorpay'),
        ('COD', 'Cash On Delivery'),
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('NotCompleted','NotCompleted')
    )
    amount_paid = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment_id} - {self.order_number}"

class CODPayment(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    otp_verified = models.BooleanField(default=False)
    otp_generated_at = models.DateTimeField(auto_now_add=True)
    
    def generate_otp(self):
        return ''.join(random.choices(string.digits, k=6))
    
    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = self.generate_otp()
        super().save(*args, **kwargs)


class TimingSlot(models.Model):
    SLOT_CHOICES = (
        ('pre_order', 'Pre order - 9-11am'),
        ('morning_delivery', 'Morning orders delivered by 12-1pm'),
        ('evening_slot', 'Evening slot 7-9pm'),
    )
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES)

    def __str__(self):
        return self.slot

class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address = models.TextField(max_length=1000)
    order_note = models.CharField(max_length=1000, blank=True)
    order_total = models.FloatField()
    tax = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    timing_slot = models.ForeignKey(TimingSlot, on_delete=models.SET_NULL, blank=True, null=True)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def order_created(self):
        return self.created_at.strftime('%B %d %Y')

    def hour_update(self):
        return self.created_at.strftime('%H:%M %p')

    def __str__(self):
        return self.first_name

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def sub_total(self):
        return self.quantity * self.product_price

    def order_created(self):
        return self.created_at.strftime('%B %d %Y')

    def __str__(self):
        return self.product.name
