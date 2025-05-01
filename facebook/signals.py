# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.core.mail import send_mail
# from django.conf import settings
# from .models import CustomUser

# @receiver(post_save, sender=CustomUser)
# def send_profile_update_email(sender, instance, created, **kwargs):
#     if not created:
#         if instance.is_profile_verified == False:
#             verification_link = f"{settings.SITE_URL}/verify-profile/{instance.pk}/" 
#             send_mail(
#                 subject="Verify Your Profile Update",
#                 message=f"Hi {instance.username},\n\nPlease verify your profile update by clicking the link below:\n{verification_link}",
#                 from_email=settings.EMAIL_HOST_USER,
#                 recipient_list=[instance.email],
#             )



# signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.core.mail import send_mail
# from django.conf import settings
# from .models import myproduct

# @receiver(post_save, sender=myproduct)
# def check_stock_and_notify(sender, instance, **kwargs):
#     if instance.stock == 0 and not instance.is_out_of_stock:
#         # Mark as out of stock to prevent multiple emails
#         instance.is_out_of_stock = True
#         instance.save(update_fields=['is_out_of_stock'])

#         # Notify seller via email
#         send_mail(
#             subject="Product Out of Stock Alert",
#             message=f"Dear {instance.seller.username},\n\nYour product '{instance.name}' is now out of stock.",
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[instance.seller.email],
#         )
#     elif instance.stock > 0 and instance.is_out_of_stock:
#         # Reset flag when stock is refilled
#         instance.is_out_of_stock = False
#         instance.save(update_fields=['is_out_of_stock'])



# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import myproduct
# from django.core.mail import send_mail

# @receiver(post_save, sender=myproduct)
# def send_out_of_stock_email(sender, instance, **kwargs):
#     if instance.stock == 0:
#         seller_email = instance.seller.user.email  # yeh seller ke through user.email assume kar raha hoon
#         send_mail(
#             subject='Product Out of Stock',
#             message=f"Dear Seller, your product '{instance.veg_name}' is out of stock.",
#             from_email='noreply@yourapp.com',
#             recipient_list=[seller_email],
#             fail_silently=True
#         )

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import myproduct
from django.core.mail import send_mail

@receiver(post_save, sender=myproduct)
def check_stock_zero(sender, instance, **kwargs):
    if instance.stock == 0:
        send_mail(
            subject='Out of Stock Alert',
            message=f'Your product "{instance.veg_name}" is now out of stock.',
            from_email='noreply@yourdomain.com',
            recipient_list=[instance.seller.email],
        )
