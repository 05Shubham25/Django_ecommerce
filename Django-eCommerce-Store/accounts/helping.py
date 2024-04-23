from django.core.mail import send_mail
from django.conf import settings

def send_forget_password_email(email, token):
    subject = 'Reset Password'
    message = f'Hi, click on link to reset your password http://127.0.0.1:8000/reset_password/{token}/'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)
    return True



# from django.conf import settings
# from twilio.rest import Client
# import random
# class Messagehandler:
#     phone_number = None
#     otp = None
#     def __init__(self,phone_number,otp):
#         self.phone_number = phone_number
#         self.otp = otp


#     def send_otp(self):
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

#         message = client.messages.create(
#             body=f'Your OTP is {self.otp}',
#             from = "+16467984830",
#             to = 

#         )