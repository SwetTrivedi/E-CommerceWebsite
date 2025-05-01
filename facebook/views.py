from django.shortcuts import render,HttpResponse,HttpResponseRedirect,redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import  redirect
import random
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from .models import CustomUser,UserOTP,Category,myproduct,subcategory,Myorders,Cart
from .forms import Myform ,OTPForm,MyProductForm,CategoryForm,SubcategoryForm,AddressForm
from .task import send_seller_status_email
from twilio.rest import Client
from django.conf import settings
from django.utils import timezone


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

from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def verify_otp(request):
    username = request.session.get('username')
    email = request.session.get('email')
    password = request.session.get('password')
    role = request.session.get('role')

    if not username or not email or not password or not role:
        return redirect('register_user')

    form = OTPForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            real_otp = request.session.get('otp')

            if real_otp:
                if entered_otp == real_otp:
                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        user_type=role,
                        is_verified=True,
                        is_active=True
                    )
                    messages.success(request, "OTP verified. You can now log in.")
                    request.session.flush() 
                    return redirect('login')
                else:
                    messages.error(request, "Invalid OTP. Please try again.")
    
    if request.method == "GET" and 'resend_otp' in request.GET:
        otp = generate_otp()
        request.session['otp'] = otp
        send_mail(
            "Your OTP Code",
            f"Your OTP code is {otp}",
            'from@example.com', 
            [email],
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

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('register_user')

        if role == 'customer':
            otp = generate_otp()
            request.session['otp'] = otp
            request.session['username'] = username
            request.session['email'] = email
            request.session['password'] = password
            request.session['role'] = role

            send_mail(
                subject='Your OTP for Account Verification',
                message=f'Your OTP is {otp}',
                from_email='your_email@gmail.com',
                recipient_list=[email],
            )
            messages.success(request, "OTP sent to your email. Please verify.")
            return redirect('verify_otp')

        elif role == 'seller':
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                user_type='seller',
                is_verified=False,
                is_active=True
            )
            # otp = generate_otp()
            # UserOTP.objects.create(user=user, otp=otp)
            # send_otp_via_sms(phone_number, otp)
            # request.session['username'] = user.username
            # messages.success(request, "OTP sent to your phone.")
            # return redirect('verify_otp')
            messages.success(request, "Registration successful. Please wait for admin approval.")
            return redirect('register_user')

        elif role == 'admin':
            user = CustomUser.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                user_type='admin',
                is_verified=True,
                is_active=True
            )
            messages.success(request, "Admin registered successfully. You can log in.")
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
                    login(request, user)
                    return redirect('seller_dashboard')

                elif role == 'customer':
                    if not user.is_active:
                        otp = generate_otp()
                        UserOTP.objects.update_or_create(user=user, defaults={'otp': otp})
                        send_mail(
                            subject='Your OTP for Account Verification',
                            message=f'Your OTP is {otp}',
                            from_email='your_email@gmail.com',
                            recipient_list=[user.email],
                        )
                        request.session['username'] = username
                        messages.error(request, "Account not verified. OTP sent to your email.")
                        return redirect('verify_otp')
                    login(request, user)
                    return redirect('customer_dashboard')

                elif role == 'admin':
                    login(request, user)
                    return redirect('admin_dashboard')

            return render(request, 'login.html', {
                'form': form,
                'error': 'Invalid username or password.'
            })
        else:
            return render(request, 'login.html', {
                'form': form,
                'error': 'Invalid form submission.'
            })

    return render(request, 'login.html',{'form':form})




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
def delete_product_admin(request, pid):
    product = get_object_or_404(myproduct, id=pid)
    product.delete()
    return redirect('admin_dashboard')


@login_required
def customer_dashboard(request):
    user = request.user

    if request.method == 'POST':
        if not user.is_profile_verified:
            messages.error(request, 'Please verify your profile update before making any further changes.')
            return redirect('customer_dashboard')

        user.username = request.POST.get('name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')

        password = request.POST.get('password')
        if password:
            user.set_password(password)

        user.save()

        messages.success(request, 'Profile updated successfully!')

   
    rdata = CustomUser.objects.get(username=request.user.username)
    return render(request, 'customer_dashboard.html', {'rdata': rdata})



@login_required
def verify_profile_update(request, pk):
    try:
        user = CustomUser.objects.get(pk=pk)
        
        if user.is_profile_verified:
            messages.info(request, 'Your profile is already verified.')
            return redirect('customer_dashboard')

       
        user.is_profile_verified = True
        user.save()

        
        send_mail(
            subject="Profile Updated Successfully",
            message=f"Hi {user.username},\n\nYour profile has been successfully updated!",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        messages.success(request, 'Your profile has been successfully verified and updated!')
        return redirect('customer_dashboard')

    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found')
        return redirect('home')







@login_required
def add_category(request):
    if request.user.user_type != 'seller':
        return redirect('home')
    
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save(commit=False)
            category.seller = request.user
            category.save()
            return redirect('seller_dashboard')
    else:
        form = CategoryForm()
    
    return render(request, 'category.html', {'form': form})


@login_required
def add_subcategory(request):
    if request.user.user_type != 'seller':
        return HttpResponse("<script>alert('Only sellers can add subcategories');location.href='/'</script>")
    
    if request.method == 'POST':
        form = SubcategoryForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('seller_dashboard')  
    else:
        form = SubcategoryForm()
    
    return render(request, 'subcategory.html',{'form':form})











@login_required
def Mycart(request):
    if request.user.user_type != 'customer':
        return HttpResponse("<script>alert('Only customers can access the cart');location.href='/'</script>")

    if request.method == "GET" and request.GET.get('qt'):
        qt = int(request.GET.get('qt',0))
        pname = request.GET.get('pname')
        ppic = request.GET.get('ppic')
        price = int(request.GET.get('price'))
        total_price = qt * price
        product = myproduct.objects.get(veg_name=pname)
        if qt > product.stock:
            return HttpResponse(f"<script>alert('Only {product.stock} item(s) in stock'); location.href='/product/';</script>")
        if qt <= 0:
            return HttpResponse("<script>alert('Add a valid product quantity'); location.href='/product/';</script>")

        if qt > 0:
            Cart.objects.create(
                user=request.user,
                product_name=pname,
                quantity=qt,
                price=price,
                total_price=total_price,
                product_picture=ppic,
                added_date=timezone.now().date()
            )
            request.session['cartitem'] = Cart.objects.filter(user=request.user).count()
            product.stock -= qt
            product.save()

            return HttpResponse("<script>alert('Your item was added successfully');location.href='/product/'</script>")
        else:
            return HttpResponse("<script>alert('Add product quantity to your cart');location.href='/product/'</script>")

    return render(request, 'mycart.html')


@login_required
def cartitem(request):
    if request.user.user_type != 'customer':
        return HttpResponse("<script>alert('Only customers can view the cart');location.href='/'</script>")

    cid = request.GET.get('cid')
    cartdata = Cart.objects.filter(user=request.user)

    if cid:
        Cart.objects.filter(id=cid, user=request.user).delete()
        request.session['cartitem'] = Cart.objects.filter(user=request.user).count()
        return HttpResponse("<script>alert('Item successfully removed');location.href='/cartitem/'</script>")

    return render(request, 'cartitem.html', {"cartdata": cartdata})

from .forms import AddressForm 


from .forms import AddressForm 
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import render_to_string
import os
from django.conf import settings
def generate_order_pdf(order_list, total_amount):
    if not order_list:
        return None

    html = render_to_string('order_reciept.html', {
        'orders': order_list,
        'user': order_list[0].user,  # use first order's user
        'address': order_list[0].address,
        'city': order_list[0].city,
        'state': order_list[0].state,
        'pin_code': order_list[0].pin_code,
        'phone_number': order_list[0].phone_number,
        'total_amount': total_amount,
    })

    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    if pisa_status.err:
        return None

    pdf_path = f'{settings.MEDIA_ROOT}/order_receipts/receipt_{order_list[0].user.id}.pdf'
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    with open(pdf_path, 'wb') as f:
        f.write(pdf_file.getvalue())

    return pdf_path



@login_required
def myorder(request):
    if request.user.user_type != 'customer':
        return HttpResponse("<script>alert('Only customers can place orders');location.href='/'</script>")

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            pin_code = form.cleaned_data['pin_code']
            phone_number = form.cleaned_data['phone_number']

            cart_items = Cart.objects.filter(user=request.user)
            total_amount = 0

            # Create orders
            order_list = []
            for item in cart_items:
                order = Myorders.objects.create(
                    user=request.user,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    price=item.price,
                    total_price=item.total_price,
                    product_picture=item.product_picture,
                    status="Pending",
                    order_date=timezone.now().date(),
                    address=address,
                    city=city,
                    state=state,
                    pin_code=pin_code,
                    phone_number=phone_number,
                )
                order_list.append(order)
                total_amount += item.total_price

            cart_items.delete()
            request.session['cartitem'] = 0

        
            pdf_path = generate_order_pdf(order_list, total_amount)

            if pdf_path:
                with open(pdf_path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'inline; filename="receipt_{request.user.id}.pdf"'
                    return response

            return HttpResponse("<script>alert('Your order has been placed successfully!');location.href='/orderslist/'</script>")
    
    else:
        form = AddressForm()

    return render(request, 'order.html', {'form':form})









@login_required
def indexcart(request):
    if request.user.user_type != 'customer':
        return HttpResponse("<script>alert('Only customers can add items to cart');location.href='/'</script>")

    if request.GET.get('qt'):
        qt = int(request.GET.get('qt'))
        pname = request.GET.get('pname')
        ppic = request.GET.get('ppic')
        price = int(request.GET.get('price'))
        total_price = qt * price

        if qt > 0:
            Cart.objects.create(
                user=request.user,
                product_name=pname,
                quantity=qt,
                price=price,
                total_price=total_price,
                product_picture=ppic,
                added_date=timezone.now().date()
            )
            request.session['cartitem'] = Cart.objects.filter(user=request.user).count()
            return HttpResponse("<script>alert('Your item was added in cart');location.href='/home/'</script>")
        else:
            return HttpResponse("<script>alert('Add product quantity to your cart');location.href='/home/'</script>")

    return render(request, 'indexcart.html')


@login_required
def orderslist(request):
    if request.user.user_type != 'customer':
        return HttpResponse("<script>alert('Only customers can view orders');location.href='/'</script>")

    oid = request.GET.get('oid')

    if oid:
        Myorders.objects.filter(id=oid, user=request.user).delete()
        return HttpResponse("<script>alert('Order canceled');location.href='/orderslist/'</script>")

    pdata = Myorders.objects.filter(user=request.user, status="Pending")
    adata = Myorders.objects.filter(user=request.user, status="Accepted")
    ddata = Myorders.objects.filter(user=request.user, status="Delivered")

    return render(request, 'orderlist.html', {
        "pdata": pdata,
        "adata": adata,
        "ddata": ddata
    })


@login_required
def delete_category(request, cid):
    category = get_object_or_404(Category, id=cid, seller=request.user)
    
    if request.user.user_type != 'seller':
        return HttpResponse("<script>alert('Unauthorized access');location.href='/'</script>")
    
    category.delete()
    return redirect('seller_dashboard')