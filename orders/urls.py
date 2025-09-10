from django.urls import path
from . import views 

app_name = 'orders'

urlpatterns = [
    path('', views.payment_method, name='payment_method'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment, name='payment'),
    # path('payments/', views.payments, name='payments'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('order_completed/', views.order_completed, name='order_completed'), 
    path('cod-payment/', views.cod_payment, name='cod_payment'),
    # path('verify-cod-otp/<str:order_number>/', views.verify_cod_otp, name='verify_cod_otp'),
     # Corrected the name of the view
    
]