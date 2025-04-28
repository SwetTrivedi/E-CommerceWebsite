from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,Category,subcategory,myproduct,Cart,Myorders

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('id', 'username', 'email', 'user_type', 'is_verified', 'is_profile_verified', 'is_staff', 'is_superuser')
    list_filter = ('user_type', 'is_verified', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('user_type', 'is_verified', 'is_profile_verified', 'phone')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Info', {
            'fields': ('user_type', 'is_verified', 'is_profile_verified', 'phone')
        }),
    )

# Register the CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(Category)
class categoryAdmin(admin.ModelAdmin):
    list_display = ('id','cname','cpic','seller','cdate')


class subcategoryAdmin(admin.ModelAdmin):
    list_display = ('id','category_name','subcategory_name')

admin.site.register(subcategory,subcategoryAdmin)


class myproductAdmin(admin.ModelAdmin):
    list_display = ('id','product_category',
                    'subcategory_name', 'veg_name','price','discount_price',
                    'product_pic','total_discount','product_quantity','pdate')

admin.site.register(myproduct,myproductAdmin)



@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id','user','product_name','quantity','price','total_price','product_picture','added_date')


@admin.register(Myorders)
class MyordersAdmin(admin.ModelAdmin):
    list_display = ('id','user','product_name','quantity','price','total_price','product_picture','status','order_date','address','city','state','pin_code','phone_number')