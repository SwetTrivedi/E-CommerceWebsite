from django.shortcuts import render,HttpResponse,HttpResponseRedirect,redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import  redirect
import random
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from .models import CustomUser,UserOTP,Category,myproduct,subcategory
from .forms import Myform ,OTPForm,MyProductForm
from .task import send_seller_status_email
from twilio.rest import Client
from django.conf import settings
def send_otp_via_sms(phone_number, otp):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Your OTP is {otp}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone_number
    )
    return message.sid



def home(request):
    data=Category.objects.all().order_by('-id')[0:18]
    md={"cdata":data}
    return render(request, 'home.html',md)

def about(request):
    return render(request,'aboutus.html')


def generate_otp():
    return str(random.randint(100000, 999999))


def verify_otp(request):
    username = request.session.get('username')
    if not username:
        return redirect('signup')

    form = OTPForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            user = CustomUser.objects.filter(username=username).first()
            if user:
                real_otp = UserOTP.objects.filter(user=user).first()
                if real_otp:
                    if real_otp.is_expired:
                        messages.error(request, "OTP has expired. Please request a new one.")
                    elif entered_otp == real_otp.otp:
                        user.is_active = True
                        user.save()
                        real_otp.delete()
                        return redirect('login')
                    else:
                        messages.error(request, "Invalid OTP. Please try again.")
    
    if request.method == "GET" and 'resend_otp' in request.GET:
        user = CustomUser.objects.filter(username=username).first()
        if user:
            otp = generate_otp()
            UserOTP.objects.update_or_create(user=user, defaults={'otp': otp})
            send_mail(
                "Your OTP Code",
                f"Your OTP code is {otp}",
                'from@example.com', 
                [user.email],
                fail_silently=False,
            )
            messages.success(request, "A new OTP has been sent to your email.")
        return redirect('verify_otp')  

    return render(request, 'verify_otp.html', {'form': form})


def register_user(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']
        phone = request.POST.get('phone')

        if role == 'customer':
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                user_type='customer',
                is_verified=True  
            )
            otp = generate_otp()
            UserOTP.objects.create(user=user, otp=otp)
            send_mail(
                subject='Your OTP for Account Verification',
                message=f'Your OTP is {otp}',
                from_email='your_email@gmail.com',
                recipient_list=[user.email],
            )
            request.session['username'] = user.username
            messages.success(request, "OTP sent to your email.")
            return redirect('verify_otp')

        elif role == 'seller':
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                user_type='seller',
                is_verified=False 
            )
            otp = generate_otp()
            UserOTP.objects.create(user=user, otp=otp)
            send_otp_via_sms(phone, otp)  # 👈 Twilio se SMS OTP bhejna
            request.session['username'] = user.username
            messages.success(request, "OTP sent to your phone.")
            return redirect('verify_otp')
            return HttpResponse("Seller registered successfully. Please wait for admin verification.")

        elif role == 'admin':
            user = CustomUser.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                user_type='admin',
                is_verified=True
            )
            return redirect('login')

        else:
            messages.error(request, "Invalid role selected.")
            return redirect('register_user')

    return render(request, 'register_user.html')


def user_login(request):
    form = Myform(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            role = request.POST.get('role')  

            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.user_type != role:
                    return render(request, 'login.html', {
                        'form': form,
                        'error': 'Invalid role selected for this account.'
                    })

                if role == 'seller':
                    if not user.is_verified:
                        return HttpResponse("Seller account not verified by admin yet.")
                    else:
                        login(request, user)
                        return redirect('seller_dashboard')
                elif role == 'customer':
                    login(request, user)
                    return redirect('customer_dashboard')
                elif role == 'admin':
                    login(request, user)
                    return redirect('admin_dashboard')
                else:
                    return render(request, 'login.html', {
                        'form': form,
                        'error': 'Invalid role.'
                    })
            else:
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Invalid username or password.'
                })
        else:
            return render(request, 'login.html', {
                'form': form,
                'error': 'Invalid form submission.'
            })

    return render(request, 'login.html', {'form': form})


def seller_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'seller':
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'admin':
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return wrapper



@login_required
@seller_required
def seller_dashboard(request):
    products = myproduct.objects.filter(seller=request.user)
    return render(request, 'seller_dashboard.html', {'products': products})

# @login_required
# def customer_dashboard(request):
#     return render(request, 'customer_dashboard.html')

@admin_required
@login_required
def admin_dashboard(request):
    sellers = CustomUser.objects.filter(user_type='seller')
    customers = CustomUser.objects.filter(user_type='customer')
    products = myproduct.objects.all()
    return render(request, 'admin_dashboard.html',{'sellers': sellers,'customers': customers,'products': products})

@login_required
def approve_seller(request, seller_id):
    if request.user.user_type != 'admin':
        return HttpResponse("Unauthorized access.")

    seller = get_object_or_404(CustomUser, id=seller_id, user_type='seller')
    seller.is_verified = True
    seller.save()
    send_seller_status_email.delay(seller.email, 'approved')
    return redirect('admin_dashboard') 

@login_required
def unapprove_seller(request, seller_id):
    if request.user.user_type != 'admin':
        return HttpResponse("Unauthorized access.")
    
    seller = get_object_or_404(CustomUser, id=seller_id, user_type='seller')
    seller.is_verified = False
    seller.save()
    send_seller_status_email.delay(seller.email, 'unapproved')
    return redirect('admin_dashboard') 

@login_required
def delete_seller(request, seller_id):
    if request.user.user_type != 'admin':
        return HttpResponse("Unauthorized access.")
    
    seller = get_object_or_404(CustomUser, id=seller_id, user_type='seller')
    seller.delete()
    return redirect('admin_dashboard') 

@login_required
def delete_customer(request, customer_id):
    if request.user.user_type != 'admin':
        return HttpResponse("Unauthorized access.")

    customer = get_object_or_404(CustomUser, id=customer_id, user_type='customer')
    customer.delete()
    return redirect('admin_dashboard')  

def user_logout(request):
    logout(request)
    return redirect('login')

def product(request):
    catid=request.GET.get('cid')
    subcatid=request.GET.get('sid')
    sdata=subcategory.objects.all().order_by('-id')
    if subcatid is not None:
        pdata=myproduct.objects.all().filter(subcategory_name=subcatid)
    elif catid is not None:
        pdata=myproduct.objects.all().filter(product_category=catid)
    else :
        pdata=myproduct.objects.all().order_by('-id')
    md={"subcat":sdata,"pdata":pdata}
    return render(request,'product.html',md)


@login_required
@seller_required
def add_product(request):
    form = MyProductForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.save()
        return redirect('seller_dashboard')
    return render(request, 'product_form.html', {'form': form})

@login_required
@seller_required
def edit_product(request, pk):
    product = get_object_or_404(myproduct, pk=pk, seller=request.user)
    form = MyProductForm(request.POST or None, request.FILES or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('seller_dashboard')
    return render(request, 'product_form.html', {'form': form,'is_edit': True})

@login_required
@seller_required
def delete_product(request, pk):
    product = get_object_or_404(myproduct, pk=pk, seller=request.user)
    product.delete()
    return redirect('seller_dashboard')


@login_required
@admin_required
def delete_product_admin(request, pk):
    product = get_object_or_404(myproduct, pk=pk)
    product.delete()
    return redirect('admin_dashboard')

@login_required
def customer_dashboard(request):
    user = request.user
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)

        user.save()
    rdata = None
    if request.user.is_authenticated:
        rdata = CustomUser.objects.get(username=request.user.username)
    md = {"rdata": rdata}
    return render(request, 'customer_dashboard.html', md)
