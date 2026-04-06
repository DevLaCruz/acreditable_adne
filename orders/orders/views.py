from django.shortcuts import render, redirect
from django.http import JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from urllib.parse import quote
from django.contrib.auth.decorators import login_required
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from decouple import config
# Create your views here.

def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])
    
    payment = Payment(
        user=request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        #amount_id = order.order_total,
        status = body['status'],
    )    
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()
    
    #mover todos los carrito items hacia la tabla order product
    cart_items=CartItem.objects.filter(user=request.user)
    
    for item in cart_items:
        orderproduct= OrderProduct()
        orderproduct.order_id=order.id
        orderproduct.payment=payment
        orderproduct.user_id=request.user.id
        orderproduct.product_id=item.product_id
        orderproduct.quantity=item.quantity
        #orderproduct.product_price=item.product.price
        orderproduct.ordered=True
        orderproduct.save()
        
        #agregando variaciones
        cart_item=CartItem.objects.get(id=item.id)
        product_variation=cart_item.variations.all()
        orderproduct=OrderProduct.objects.get(od=orderproduct.id)
        orderproduct.variation.set(product_variation)
        orderproduct.save()
        
        
        product=Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
        
    CartItem.objects.filter(user=request.user).delete()
    
    mail_subject='Gracias por tu compra'
    body=render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order':order,
    })
    
    to_email=request.user.mail
    send_email=EmailMessage(mail_subject, body, to=[to_email])
    send_email.send()
    
    data = {
        'order_number': order.order_number,
        'transID':payment.payment_id,
    }
    
    return JsonResponse(data)



# def place_order(request, total=0, quantity=0):
#     current_user = request.user
#     cart_items = CartItem.objects.filter(user=current_user)
#     cart_count = cart_items.count()

#     if cart_count <= 0:
#         return redirect('store')

#     # grand_total = 0
#     # tax = 0

#     # for cart_item in cart_items:
#     #     total += (cart_item.product.price * cart_item.quantity)
#     #     quantity += cart_item.quantity

#     # tax = (2 * total)/100
#     # grand_total = total + tax

#     if request.method == 'POST':
#         form = OrderForm(request.POST)

#         if form.is_valid():
#             data = Order()
#             data.user = current_user
#             data.first_name = form.cleaned_data['first_name']
#             data.last_name = form.cleaned_data['last_name']
#             data.phone = form.cleaned_data['phone']
#             data.dni = form.cleaned_data['dni']
#             data.address_line_1 = form.cleaned_data['address_line_1']
#             data.address_line_2 = form.cleaned_data['address_line_2']
#             data.country = form.cleaned_data['country']
#             data.state = form.cleaned_data['state']
#             data.city = form.cleaned_data['city']
#             data.order_note = form.cleaned_data['order_note']
#             data.order_total = grand_total
#             data.tax = tax
#             data.ip = request.META.get('REMOTE_ADDR')

#             yr=int(datetime.date.today().strftime('%Y'))
#             mt=int(datetime.date.today().strftime('%m'))
#             dt=int(datetime.date.today().strftime('%d'))
#             d = datetime.date(yr,mt,dt)
#             current_date = d.strftime("%Y%m%d")
#             # 20280110
#             order_number = current_date + str(data.id)
#             data.order_number = order_number
#             data.save()

#             order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
#             context = {
#                 'order': order,
#                 'cart_items': cart_items,
#                 # 'total' : total,
#                 # 'tax': tax,
#                 # 'grand_total': grand_total,
#             }

#             #return render(request, 'orders/payments.html', context)
#             # Format WhatsApp message
#             message = format_whatsapp_message(context)
#             context['whatsapp_url'] = f"https://wa.me/51988690314?text={quote(message)}"
            
#             # Store in session for quote_success
#             request.session['quote_context'] = context
            
#             # Clear cart
#             cart_items.delete()

#             return redirect('quote_success')
#     else:
#         return redirect('checkout')    

def place_order(request, quantity=0):
    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            data = Order()
            data.user = request.user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.dni = form.cleaned_data['dni']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = 0  # Set default or remove if nullable
            data.tax = 0  # Set default or remove if nullable
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            mt = int(datetime.date.today().strftime('%m'))
            dt = int(datetime.date.today().strftime('%d'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            cart_items = CartItem.objects.filter(user=request.user)
            context = {
                'order': data,
                'cart_items': cart_items,
            }

            message = format_whatsapp_message(form.cleaned_data, cart_items)
            whatsapp_url = f"https://wa.me/51988690314?text={quote(message)}"
            request.session['whatsapp_url'] = whatsapp_url
            
            cart_items.delete()
            return redirect('quote_success')
        else:
            return redirect('checkout')  

def format_whatsapp_message(form_data, cart_items):
    message = "NUEVA COTIZACIÓN\n\n"
    message += "DATOS DEL CLIENTE:\n"
    message += f"Nombre: {form_data['first_name']} {form_data['last_name']}\n"
    message += f"Teléfono: {form_data['phone']}\n"
    message += f"DNI: {form_data['dni']}\n\n"
    message += f"DIRECCIÓN DE ENTREGA:\n"
    message += f"{form_data['address_line_1']}"
    if form_data['address_line_2']:
        message += f" {form_data['address_line_2']}"
    message += f"\n{form_data['city']}, {form_data['state']}, {form_data['country']}\n\n"
    message += "PRODUCTOS:\n"
    
    # Base URL for product details
    base_url = config('BASE_URL') # Change in production
    
    for item in cart_items:
        product = item.product
        product_url = base_url + product.get_url()
        image_url = base_url + product.images.url if product.images else ""
        
        message += f"\n* {item.quantity}x {product.product_name}\n"
        if item.variations.exists():
            for variation in item.variations.all():
                message += f"  - {variation.variation_category}: {variation.variation_value}\n"
        message += f"Ver producto: {product_url}\n"
        if image_url:
            message += f"Imagen: {image_url}\n"
    
    if form_data.get('order_nota'):
        message += f"\nNota adicional:\n{form_data['order_nota']}\n"
    
    return message


@login_required(login_url='login')
def quote_success(request):
    whatsapp_url = request.session.get('whatsapp_url')
    if not whatsapp_url:
        return redirect('store')
    
    # Clear session after getting URL
    del request.session['whatsapp_url']
    
    return render(request, 'orders/quote_success.html', {
        'whatsapp_url': whatsapp_url
    })


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        # subtotal = 0
        # for i in ordered_products:
        #     subtotal += i.product_price*i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            #'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
    