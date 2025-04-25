from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about,name='aboutus'),
    path('register/', views.register_user, name='register_user'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/seller/', views.seller_dashboard, name='seller_dashboard'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('approve_seller/<int:seller_id>/', views.approve_seller, name='approve_seller'),
    path('unapprove-seller/<int:seller_id>/', views.unapprove_seller, name='notapprove_seller'),
    path('delete-seller/<int:seller_id>/', views.delete_seller, name='delete_seller'),
    path('delete_customer/<int:customer_id>/', views.delete_customer, name='delete_customer'),
    path('product/',views.product,name='products'),
    path('seller/add/', views.add_product, name='add_product'),
    path('seller/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('seller/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('admin/delete/<int:pk>/', views.delete_product_admin, name='delete_product_admin'),
    path('verify-profile/<int:pk>/', views.verify_profile_update, name='verify_profile_update'),
]