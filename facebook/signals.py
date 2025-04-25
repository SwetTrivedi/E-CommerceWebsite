from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def send_profile_update_email(sender, instance, created, **kwargs):
    if not created:
        if instance.is_profile_verified == False:
            verification_link = f"{settings.SITE_URL}/verify-profile/{instance.pk}/" 
            send_mail(
                subject="Verify Your Profile Update",
                message=f"Hi {instance.username},\n\nPlease verify your profile update by clicking the link below:\n{verification_link}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[instance.email],
            )

