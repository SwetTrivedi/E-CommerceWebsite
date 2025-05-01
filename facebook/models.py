from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
class CustomUser(AbstractUser):
    USER_ROLES = (
        ('admin', 'Admin'),
        ('seller', 'Seller'),
        ('customer', 'Customer'),
    )
    user_type = models.CharField(max_length=10, choices=USER_ROLES)
    is_verified = models.BooleanField(default=False)
    is_profile_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, null=True, blank=True)
    def __str__(self):
        return f"{self.username} ({self.user_type})"

class UserOTP(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"
    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=2)
    

class Category(models.Model):
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True,blank=True)
    cname=models.CharField(max_length=200,null=True)
    cpic=models.ImageField(upload_to='static/category/',null=True)
    cdate=models.DateField()
    def __str__(self):
        return  self.cname
    
class subcategory(models.Model):
    category_name=models.ForeignKey(Category,on_delete=models.CASCADE)
    subcategory_name=models.CharField(max_length=100,null=True)

    def __str__(self):
        return self.subcategory_name
    

class myproduct(models.Model):
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True,blank=True)
    product_category=models.ForeignKey(Category,on_delete=models.CASCADE)
    subcategory_name=models.ForeignKey(subcategory,on_delete=models.CASCADE)
    veg_name=models.CharField(max_length=200,null=True)
    price=models.IntegerField()
    discount_price=models.IntegerField()
    product_pic=models.ImageField(upload_to='static/product/',null=True)
    total_discount=models.IntegerField()
    product_quantity = models.CharField(max_length=200)
    stock = models.PositiveIntegerField(default=0)
    # is_out_of_stock = models.BooleanField(default=False)
    pdate=models.DateField()
    


class Cart(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    product_name=models.CharField(max_length=200)
    quantity=models.IntegerField(null=True)
    price=models.IntegerField(null=True)
    total_price=models.FloatField(null=True)
    product_picture=models.CharField(max_length=300,null=True)
    pw=models.CharField(max_length=200,null=True)
    added_date=models.DateField()
    
    def _str_(self):
        return f"{self.product_name} x {self.quantity} for {self.user}"

class Myorders(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField(null=True)
    price = models.IntegerField(null=True)
    total_price = models.FloatField(null=True)
    product_picture = models.CharField(max_length=300, null=True)
    order_date = models.DateField(null=True)
    status=models.CharField(max_length=200,null=True,default="Pending")
    address = models.TextField(null=True)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=100, null=True)
    pin_code = models.CharField(max_length=10, null=True)
    phone_number = models.CharField(max_length=15, null=True)

    def _str_(self):
        return f"Order by {self.user} - {self.product_name} ({self.status})"
