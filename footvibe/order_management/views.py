from django.shortcuts import render,redirect,get_object_or_404,HttpResponse
from order_management.models import *
from cart_management.models import *
from home.models import *
from datetime import datetime
import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
import razorpay
from django.conf import settings
from django.http import HttpResponseRedirect

# Create your views here.

@login_required(login_url='log:user_login')
def order_placed(request, total=0, quantity=0):
   
    if not request.user.is_authenticated:
        return redirect('log:index')

    current_user = request.user
    cart_items = CartItem.objects.filter(cart__user=current_user)

    grand_total = 0
    tax = 0

    for cart_item in cart_items:
        total += (cart_item.product_variant.sale_price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax


    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty. Add items to your cart before placing an order.')
        return redirect('cart_mng:cart')

    if request.method == 'POST':
        selected_payment_option = request.POST.get('payment_option')
        print(request,'this is requeest----------------------------')
        try:
            print("yoooooo")
            address = AddressBook.objects.get(user=request.user, is_default=True)
            print(address)
        except AddressBook.DoesNotExist:
            messages.warning(request, 'No delivery address exists! Add an address and try again')
            print("\n\n\n\n\n\n\n ismath \n\n\n")
            return redirect('log:checkout')

        data = Order()
        data.user = current_user
        data.first_name = address.first_name
        data.last_name = address.last_name
        data.phone = address.phone
        data.email = address.email
        data.address_line_1 = address.address_line_1
        data.city = address.city
        data.state = address.state
        data.country = address.country
        data.pincode = address.pincode
        data.order_total = grand_total
        data.tax = tax
        data.ip = request.META.get('REMOTE_ADDR')
        data.save()
        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr, mt, dt)
        current_date = d.strftime("%Y%m%d")
        order_number = current_date + str(data.id)
        data.order_number = order_number
        data.is_ordered = True
        data.save()

        if selected_payment_option == "CashOnDelivery":
            print("Selected Payment Method:", selected_payment_option)

            payment_id = f'uw{data.order_number}{data.id}'
            payment_status = 'COMPLETED' if selected_payment_option == 'CashOnDelivery' else 'Pending'
            payment = Payment.objects.create(
                user=current_user, 
                payment_method=selected_payment_option,
                payment_id=payment_id,
                amount_paid=data.order_total,
                status=payment_status
            )
            payment.save()
            data.payment = payment
            data.save()

            ordered_products = []

            for cart_item in cart_items:
                ordered_product = OrderProduct.objects.create(
                    user=current_user,
                    order=data,
                    payment=payment,
                    product=cart_item.product_variant.product,
                    quantity=cart_item.quantity,
                    ordered=True,
                    product_variant=cart_item.product_variant,
                )
                ordered_products.append(ordered_product)

            cart_items.delete()
            variant = ProductVariant.objects.filter(product = ordered_product.product)
            context = {
                'order': data,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'ordered_products': ordered_products,
                'variant': variant,
            }

            request.session['order_id'] = data.id

        
            return render(request, "user/order_placed.html", context)

        elif selected_payment_option == "RAZORPAY":
                # Initialize Razorpay client with your API key and secret
                client = razorpay.Client(auth=(settings.RAZOR_PAY_KEY, settings.SECRET_KEY))

                # Create a Razorpay order
                order_amount_paise = int(data.order_total * 100)  # Convert order total to paise
                order_currency = 'INR'  # Change this if you are using a different currency
                order_receipt = f'order_{data.order_number}'  # You can customize the order receipt

                razorpay_order = client.order.create({
                    'amount': order_amount_paise,
                    'currency': order_currency,
                    'receipt': order_receipt,
                    
                    # Add other optional parameters as needed
                })

                print(razorpay_order)

                context = {
                    'order': data,
                    'total': total,
                    'tax': tax,
                    'grand_total': grand_total,
                    'razorpay_order': razorpay_order,
                    'razorpay_key': settings.RAZOR_PAY_KEY,
                }

                return render(request, "user/payment.html", context)


    return redirect('log:checkout')





def payment(request):
    current_user = request.user
    payment_method = request.GET.get('method')
    print(payment_method)
    payment_id = request.GET.get('payment_id')
    payment_order_id = request.GET.get('payment_order_id')
    order_id = request.GET.get('order_id')


  
    if not current_user.is_authenticated:
        return HttpResponse("User must be logged in for online payment")

    # Get order details
    try:

        order_id_session = request.session.get('order_id')
        if not order_id_session:
            raise Order.DoesNotExist

        order = Order.objects.get(order_number=order_id, user=current_user)
    except Order.DoesNotExist:
        return HttpResponse("Order not found")

    # Get ordered products for the order
    ordered_products = OrderProduct.objects.filter(order=order)

    # Calculate total amount (you might need to adjust this based on your models)
    total_amount = order.order_total
    print(f"Debug: Total amount in payment view: {total_amount}")

    payment_status = 'COMPLETED'
    payment = Payment.objects.create(
        user=current_user, 
        payment_method=payment_method,
        payment_id=payment_id,
        amount_paid=total_amount,
        status=payment_status
    )
    payment.save()
    order.payment = payment
    order.save()


    ordered_products = []
    cart_items = CartItem.objects.filter(cart__user=current_user)
    for cart_item in cart_items:
        ordered_product = OrderProduct.objects.create(
            user=current_user,
            order=order,
            payment=payment,
            product=cart_item.product_variant.product,
            quantity=cart_item.quantity,
            ordered=True,
            product_variant=cart_item.product_variant,
        )
        ordered_products.append(ordered_product)

    cart_items.delete()


    # You can pass additional context data if needed
    context = {
        'order': order,
        'ordered_products': ordered_products,
        'total_amount': total_amount,
        'payment_method':payment_method,
        'payment_id':payment_id,
        'payment_order_id':payment_order_id,
        
    }
    print(f"Debug: Total amount in payment view: {total_amount}")


    return render(request, "user/order_placed.html", context)




def ordered_detail(request, order_id):
    current_user = request.user

    try:
        order = Order.objects.get(id=order_id, user=current_user)
    except Order.DoesNotExist:

        return HttpResponse("Order not found")

    ordered_products = OrderProduct.objects.filter(order=order)

    context = {
        'order': order,
        'ordered_products': ordered_products,

    }
    return render(request, 'user/ordered_detail.html', context)






# @login_required(login_url='log:user_login')
# def my_orders(request):

#     if not request.user.is_authenticated:
#         return redirect('log:index')
    
#     orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
#     order_products = OrderProduct.objects.filter(order__in=orders)
#     context = {
#         'orders': orders,
#         "order_products":order_products
#     }
  
#     return render(request, 'user/order.html', context)




# @login_required(login_url='log:user_login')
# def cancel_order(request, order_id):
#     order = Order.objects.get(id=order_id)

#     if order.status == 'Delivered':
#         # Update the order status to 'Cancelled'
#         order.status = 'Cancelled'
#         order.save()

#         # Optional: Implement stock adjustments if needed
#         # Example: Increment stock for variations
#         for order_product in order.orderproduct_set.all():
#             if order_product.variations.exists():
#                 for variation in order_product.variations.all():
#                     variation.stock += order_product.quantity
#                     variation.save()

#         messages.warning(request, 'Cancel request has been sent.')

#     else:
#         messages.warning(request, 'Cancel request cannot be processed.')

#     return redirect('order_mng:order')



# @login_required(login_url='log:user_login')
# def cancel_order(request, order_id):
#     order = get_object_or_404(Order, id=order_id)

#     if order.status == 'Delivered':
#         # Update the order status to 'Cancelled'
#         order.status = 'Cancelled'
#         order.save()

#         # Optional: Implement stock adjustments if needed
#         # Example: Increment stock for variations
#         for order_product in order.orderproduct_set.all():
#             if order_product.variations.exists():
#                 for variation in order_product.variations.all():
#                     variation.stock += order_product.quantity
#                     variation.save()

#         messages.warning(request, 'Cancel request has been sent.')

#     else:
#         messages.warning(request, 'Cancel request cannot be processed.')

#     return redirect('order_mng:order')



@login_required(login_url='log:user_login')
def cancel_order(request, order_id):
    try:
        # Fetch the order
        order = Order.objects.get(id=order_id, user=request.user)

        # If the order is not already canceled, proceed with cancellation
        if order.status != 'Cancelled':
            # Update the order status to 'Cancelled'
            order.status = 'Cancelled'
            order.save()

            # Check if the order has associated payment
            if order.payment:
                # Update the payment status to 'Cancelled'
                order.payment.status = 'Cancelled'
                order.payment.save()

            # You may want to handle the cancellation of ordered products here if needed

            # Redirect to the referring page or a default page
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        else:
            messages.warning(request, 'Order is already cancelled.')

    except Order.DoesNotExist:
        messages.warning(request, 'Order not found.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def update_status(request):
    if request.method == "POST":
        order_id = request.POST.get('OrderID')
        status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)

        # Update the order status
        order.status = status
        order.save()
        print(order.status, order.order_number)
    # return redirect('orders:admn_product_order')
        return redirect('log:order')





