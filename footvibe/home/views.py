from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User,auth
from django.http import HttpResponseNotFound
from django.contrib import messages
from home.models import Account,AddressBook
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.core.mail import send_mail
import random,re
from django.core.exceptions import ObjectDoesNotExist
from product_management.models import *
from django.contrib.auth import update_session_auth_hash
from home.forms import AddressForm
from cart_management.models import *
from django.db.models import Sum
from order_management.models import *
from django.core.validators import validate_email, validate_integer
from django.core.exceptions import ValidationError

# Create your views here.
    
def index(request):
    variants = []
    products = Product.objects.filter(is_active = True)

    for product in products:
        prod_variants = ProductVariant.objects.filter(product = product, is_active = True)
        if prod_variants:
            variants.append(prod_variants[0])

    context = {
        'products': variants,
    }

    return render(request, 'user/index.html',context)

def user_login(request):
    if request.user.is_authenticated:
        return redirect('log:index')
    
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
     

        if user is not None:
            login(request, user)
            messages.success(request, 'You are logged in successfully')
            return redirect('log:index')
        
        if not Account.objects.filter(email=email).exists():
            messages.error(request,"There is not such a user")
            return redirect('log:user_login')
        if Account.objects.filter(email=email,is_active=False).exists():
            messages.error(request,"You are Blocked By Admin, Please contact Admin")
            return redirect('log:user_login')
        else:
            messages.error(request, 'Login failed. Please check your email and password.')

    return render(request, 'user/user_login.html')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_signup(request):
    if request.user.is_authenticated:
        return redirect('log:index')
    
    if request.method=='POST':
        user=request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')
        print('email',email)
        print('pass',password)
        
        if  Account.objects.filter(username=user).exists():
            messages.error(request, "Username already existing")
            return redirect('log:user_signup')
        

        if  Account.objects.filter(email=email).exists():
            messages.error(request, "Email Address already existing")
            return redirect('log:user_signup')
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, "Invalid email")
            return redirect('log:user_signup')
        
        if not re.match(r'^[\w.@+-]+$', user):
            messages.error(request, "Invalid username")
            return redirect('log:user_signup')
        
        if not re.match(r'^\d{10}$', phone):
            messages.error(request, "Invalid phone number. Please enter a 10-digit phone number.")
            return redirect('log:user_signup')

        
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('log:user_signup')
        
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters")
            return redirect('log:user_signup')
        
        user=Account.objects.create_user(email=email, password=password,username=user,phone=phone)
        user.save()

        # Add success message
        messages.success(request, 'Signup successful. Please check your email for OTP verification.')



        request.session['email']=email
        return redirect('log:send_otp')
        

    else:
        
        return render(request,'user/user_signup.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def send_otp(request):

    random_num=random.randint(1000,9999)
    request.session['OTP_Key']=random_num


    send_mail(
        "OTP AUTHENTICATING footvibe",
        f"{random_num} -OTP",
        "ismathrm9@gmail.com",
        [request.session['email']],
        fail_silently=False,
    )

    print(random_num)
    return redirect('log:verify_otp')

def verify_otp(request):
    print('hiii')
    user=Account.objects.get(email=request.session['email'])
    if request.method=="POST":

        if str(request.session['OTP_Key']) != str(request.POST['otp']):
            print(request.session['OTP_Key'],request.POST['otp'])
            messages.error(request, "wrong OTP. Please enter the correct OTP")

        else:
            user.is_active=True
            user.save()
            # login(request,user)
            print("helo")
            messages.success(request, "OTP has been verified successfully!")
            return redirect('log:user_login')
            
    return render(request,'user/otp_verification.html')


@login_required(login_url='log:user_login')
def user_logout(request):
    logout(request)
    messages.success(request, "your logout is successfull")
    return redirect('log:index')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def forgot_password(request):
    if request.method == "POST":

        email=request.POST["email"]
        pass1=request.POST["password"]
        pass2=request.POST["conform_password"]

        if pass1 != pass2:
            messages.error(request,"Passwords do not match.")
            return redirect('user_log/forgot_password.html')
        try:
            user = Account.objects.get(email=email)
        except ObjectDoesNotExist:
            messages.warning(request, "your user email not available, plese enter a valid email")
        request.session['email']=email
        request.session['password']=pass1
        return redirect('log:sent_otp_forgot_password') 
    else:
         return render(request,'user/forgot_password.html')
    
    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def sent_otp_forgot_password(request):
   random_num=random.randint(1000,9999)
   print(random_num)
   request.session['OTP_Key']=random_num
   send_mail(
   "OTP AUTHENTICATING footvibe",
   f"{random_num} -OTP",
   "ismathrm9@gmail.com",
   [request.session['email']],
   fail_silently=False,
    )
   return redirect('log:verify_otp_forgot_password')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def verify_otp_forgot_password(request):
    user=Account.objects.get(email=request.session['email'])

    if request.method=="POST":
      if str(request.session['OTP_Key']) != str(request.POST['otp']):
         print(request.session['OTP_Key'],request.POST['otp'])
         messages.error(request, "wrong OTP. Please enter the correct OTP")
         return redirect('log:verify_otp_forgot_password')
      else:
         password=request.session['password']
         user.set_password(password)
         user.save()
         login(request,user)
         messages.success(request, "Password changed successfully!")
         return redirect('log:user_login')
    return render(request,'user/otp_verification.html')



def resend_otp(request):
    
    
    random_num=random.randint(1000,9999)
    print(random_num)
    request.session['OTP_Key']=random_num
    send_mail(
    "OTP AUTHENTICATING footvibe",
    f"{random_num} -OTP",
    "ismathrm9@gmail.com",
    [request.session['email']],
    fail_silently=False,
    )
    messages.success(request, "OTP has been resent successfully!")
    return redirect('log:verify_otp')





def product_detail(request, variant_slug=None):
    
    try:
        single_product = get_object_or_404(ProductVariant, product_variant_slug=variant_slug)
        # print(single_product, "single_product")
        print(single_product.product_variant_slug)

        product = ProductVariant.objects.get(product_variant_slug=variant_slug).product

        product_variants = ProductVariant.objects.filter(product=single_product.product)

        attribute_values = [product_variant.attribute_value.all() for product_variant in product_variants]
        # print([product for product in attribute_values])

    except ProductVariant.DoesNotExist:
        return HttpResponseNotFound("Product not found")

    product_images = [image.image for image in single_product.product_images.all()]
    product_images.insert(0, single_product.thumbnail_image)
    # print(attribute_values)

    # Extract colors and sizes from attribute values.
    # color = [i[0] for i in attribute_values]
    # print("asdfads", color)
    # size = [i[0] for i in attribute_values]
    color = Attribute_Value.objects.filter(attribute = 10)
    size = Attribute_Value.objects.filter(attribute = 11)

    context = {
        'single_product': single_product,
        'product_images': product_images,
        'product_variant': product_variants,
        'attribute_values': attribute_values,
        'color': color,
        'size': size,
    }
    return render(request, 'user/product_detail.html', context)




# ..........................................shop..........................................#

def shop(request):
    sort_by = request.GET.get('sort_by', 'price_low_high')  
    print(f'Sort by: {sort_by}')

    variants = []
    products = Product.objects.filter(is_active = True)
    categories = Category.objects.all()
    print(products)

    for product in products:
        prod_variants = ProductVariant.objects.filter(product = product, is_active = True)
        if prod_variants:
            variants.append(prod_variants[0])

    if sort_by == 'price_low_high':
        variants = sorted(variants, key=lambda x: x.sale_price)
    elif sort_by == 'price_high_low':
        variants = sorted(variants, key=lambda x: x.sale_price, reverse=True)
    


    context = {
        'products': variants,
        'categories': categories,
        'current_sort': sort_by,
    }

    return render(request,'user/shop.html',context)





def shop_category(request,slug):
    categorires = Category.objects.all()
    products = ProductVariant.objects.filter(product__product_catg__slug=slug)
    print(categorires)
    context = {
        'products': products,
        'categories':categorires,
    }
    return render(request, "user/shop.html", context)




#......................................profile........................................#

@login_required(login_url='log:user_login')
def user_profile(request):
    try:
        user_profile = Account.objects.get(email=request.user.email)
        addresses = AddressBook.objects.filter(user=user_profile)
        orders= Order.objects.filter(user=user_profile)
       
    except Account.DoesNotExist:
        messages.error(request, "User profile not found.")
        return render(request, 'user/user_profile.html')

    context = {
        'user_profile': user_profile,
        'addresses': addresses,
        'orders':orders,
    }
    return render(request, 'user/user_profile.html', context)





def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('log:index')

    user = request.user

    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        number = request.POST.get('number')

        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, "Invalid email")
            return render(request, "user/edit_profile.html", {'user': user})

        # Validate username format (only letters)
        if not re.match(r'^[a-zA-Z]+$', username):
            messages.error(request, "Invalid username. Use only letters.")
            return render(request, "user/edit_profile.html", {'user': user})

        # Validate phone number format
        if not re.match(r'^\d{10}$', number):
            messages.error(request, "Invalid phone number. Please enter a 10-digit phone number.")
            return render(request, "user/edit_profile.html", {'user': user})

        # Update user fields
        user.email = email
        user.username = username
        user.phone = number

        # Save the user object
        user.save()

        messages.success(request, "Profile updated successfully")
        return redirect('log:user_profile')

    return render(request, "user/edit_profile.html", {'user': user})


#................................................Address..........................................................#



def add_address(request, source=None):
    print(source)
    
    print(request.path)
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            new_address = form.save(commit=False)
            new_address.user = request.user  
            new_address.save()

            messages.success(request, 'Address added successfully.')

            if source == 'user_profile':
                return redirect('log:user_profile')
            elif source == 'checkout':
                return redirect ('log:checkout')
                  
        else:
            messages.error(request, 'Error adding address. Please check the form.')

            if source == 'user_profile':
                return redirect('log:add_address',source)
            elif source == 'checkout':
                return redirect ('log:checkout')

    else:
        form = AddressForm()

    return render(request, 'user/add_address.html', {'form': form})






def edit_address(request, address_id):
    address = get_object_or_404(AddressBook, pk=address_id)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            edited_address = form.save(commit=False)
            edited_address.user = request.user  
            edited_address.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('log:user_profile')
        else:
            messages.error(request, 'Error updating address. Please correct the errors below.')
    else:
        form = AddressForm(instance=address)

    return render(request, 'user/edit_address.html', {'form': form, 'address': address})




def set_default_address(request, address_id):

    AddressBook.objects.filter(user=request.user).exclude(pk=address_id).update(is_default=False)

    address = AddressBook.objects.get(pk=address_id)
    address.is_default = True
    address.save()

    return redirect('log:user_profile')




def checkout(request):
    try:
        tax = 0
        grand_total = 0
        total = 0
        quantity = 0

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(cart__user=request.user)
            active_carts = Cart.objects.filter(cartitem__in=cart_items).distinct()

            cart_items = CartItem.objects.filter(cart__in=active_carts)

            for cart_item in cart_items:
                total += (cart_item.product_variant.sale_price * cart_item.quantity)
                quantity += cart_item.quantity

            tax = (2 * total) / 100
            grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    form = AddressForm(request.POST) if request.method == 'POST' else AddressForm()
    address_list = AddressBook.objects.filter(user=request.user)

    user_cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = user_cart.cartitem_set.all()

    context = {
        'form': form,
        'address_list': address_list,
        'cart_items': cart_items,
        'total': total,
        'quantity': quantity,
        'tax': tax,
        'grand_total': grand_total,
    }

    

    return render(request, 'user/checkout.html', context)
