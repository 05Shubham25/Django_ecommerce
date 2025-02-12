from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, Order, OrderProduct, TimingSlot

class OrderProductInline(admin.TabularInline):
    def thumbnail(self, object):
        if object.product and object.product.image:
            return format_html('<img style="border-radius:10px; width:100px; height:100px" src="{}">', object.product.image.url)
        return format_html('<span style="color: red;">No Image</span>')

    def amount(self, object):
        if object.product_price is not None and object.quantity is not None:
            amount = float(object.product_price * object.quantity)
            return format_html('₹{}', '{:.2f}'.format(amount))
        return format_html('<span style="color: red;">N/A</span>')

    thumbnail.short_description = 'Product Picture'
    amount.short_description = 'Amount'

    model = OrderProduct
    readonly_fields = ['thumbnail', 'product', 'variations', 'product_price', 'quantity', 'user', 'payment', 'ordered', 'amount']
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'user', 'payment_method', 'amount_paid', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'payment_method', 'created_at']
    search_fields = ['payment_id', 'user__email', 'user__first_name']
    list_per_page = 20
    readonly_fields = ['payment_id', 'user', 'payment_method', 'amount_paid', 'created_at']
    ordering = ['-created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def payment_status(self, obj):
        if obj.payment:
            status = obj.payment.payment_status
            status_colors = {
                'Completed': ('green', '✓ Completed'),
                'NotCompleted': ('red', '✗ Not Completed'),
            }
            color, text = status_colors.get(status, ('orange', f'⋯ {status}'))
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)
        return format_html('<span style="color: gray;">No payment</span>')

    def order_total_display(self, obj):
        if obj.order_total is not None:
            total = float(obj.order_total)
            return format_html('₹{}', '{:.2f}'.format(total))
        return format_html('<span style="color: red;">N/A</span>')

    list_display = [
        'order_number', 
        'full_name', 
        'email', 
        'phone', 
        'order_total_display', 
        'payment_status',
        'timing_slot',
        'status', 
        'is_ordered',
        'created_at'
    ]
    list_filter = ['is_ordered', 'status', 'timing_slot', 'created_at']
    list_per_page = 20
    ordering = ['-created_at']
    inlines = [OrderProductInline]
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
    readonly_fields = ['payment', 'order_number', 'order_total', 'tax', 'ip', 'is_ordered', 'created_at', 'updated_at']
    autocomplete_fields = ['user', 'payment']

    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Order Information', {
            'fields': ('order_number', 'order_total', 'tax', 'status', 'is_ordered', 'timing_slot')
        }),
        ('Delivery Information', {
            'fields': ('address', 'order_note')
        }),
        ('Payment Information', {
            'fields': ('payment',)
        }),
        ('Additional Information', {
            'fields': ('ip', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    order_total_display.short_description = 'Order Total'
    payment_status.short_description = 'Payment Status'


@admin.register(TimingSlot)
class TimingSlotAdmin(admin.ModelAdmin):
    list_display = ['slot']
    list_filter = ['slot']