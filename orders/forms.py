from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    selected_timing_slot = forms.CharField(max_length=20, required=False)  # Add this field

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'order_note']
