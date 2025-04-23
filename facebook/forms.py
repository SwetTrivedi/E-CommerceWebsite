from django import forms
from captcha.fields import CaptchaField
from .models import myproduct
class OTPForm(forms.Form):
    otp = forms.CharField(
        label="Enter OTP",
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 6-digit OTP'})
    )
    
class Myform(forms.Form):
    captcha=CaptchaField()


class MyProductForm(forms.ModelForm):
    class Meta:
        model = myproduct
        exclude= ['seller']