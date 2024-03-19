from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from onlinepayments.sdk.communicator import Communicator
from onlinepayments.sdk.defaultimpl.default_authenticator import DefaultAuthenticator
from onlinepayments.sdk.defaultimpl.default_connection import DefaultConnection
from onlinepayments.sdk.domain.amount_of_money import AmountOfMoney
from onlinepayments.sdk.domain.create_hosted_checkout_request import CreateHostedCheckoutRequest
from onlinepayments.sdk.domain.create_payment_request import CreatePaymentRequest
from onlinepayments.sdk.domain.hosted_checkout_specific_input import HostedCheckoutSpecificInput
from onlinepayments.sdk.meta_data_provider import MetaDataProvider
from onlinepayments.sdk.domain.order import Order

from marketplace.models import Cart, Tax
from marketplace.context_processors import get_cart_amounts
from menu.models import FoodItem
from orders.forms import OrderForm
from orders.models import Order, Payment, OrderedFood
from .utils import generate_order_number, order_total_by_vendor
from accounts.utils import send_notification
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from foodonline_main.settings import STRIPE_API_KEY
from foodonline_main.settings import KLARNA_MID
from foodonline_main.settings import W_API_KEY_ID
from foodonline_main.settings import W_SECRET_API_KEY
from foodonline_main.settings import MERCHANT_ID
from decimal import Decimal
from onlinepayments.sdk.factory import Factory


import simplejson as json
import stripe


stripe.api_key = STRIPE_API_KEY

@login_required(login_url='login')
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('marketplace')
    print(cart_count)
    vendors_ids = []
    for i in cart_items:
        if i.fooditem.vendor.id not in vendors_ids:
            vendors_ids.append(i.fooditem.vendor.id)

    # {"vendor_id":{"subtotal":{"tax_type": {"tax_percentage": "tax_amount"}}}}
    subtotal = 0
    k = {}
    get_tax = Tax.objects.filter(is_active=True)
    total_data = {}
    for i in cart_items:
        fooditem = FoodItem.objects.get(pk=i.fooditem.id, vendor_id__in=vendors_ids)
        v_id = fooditem.vendor.id
        if v_id in k:
            subtotal = k[v_id]
            subtotal += (fooditem.price * i.quantity)
        else:
            subtotal = (fooditem.price * i.quantity)
            k[v_id] = subtotal

        #calculate tax_data
        tax_dict = {}
        for i in get_tax:
            tax_type = i.tax_type
            tax_percentage = i.tax_percentage
            tax_amount = round((tax_percentage * subtotal) / 100, 2)
            tax_dict.update({tax_type: {str(tax_percentage): str(tax_amount)}})
            # Construct total data
        total_data.update({fooditem.vendor.id: {str(subtotal): str(tax_dict)}})

    subtotal = get_cart_amounts(request)['subtotal']
    grand_total = get_cart_amounts(request)['grand_total']
    tax = get_cart_amounts(request)['tax']
    total_tax = get_cart_amounts(request)['tax']
    tax_data = get_cart_amounts(request)['tax']

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order()
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.email = form.cleaned_data['email']
            order.phone = form.cleaned_data['phone']
            order.GSM = form.cleaned_data['GSM']
            order.address = form.cleaned_data['address']
            order.huis_number = form.cleaned_data['huis_number']
            order.bus_number = form.cleaned_data['bus_number']
            order.city = form.cleaned_data['city']
            order.country = form.cleaned_data['country']
            order.pin_code = form.cleaned_data['pin_code']
            order.user = request.user
            order.total = grand_total
            order.tax = json.dumps(tax)
            order.tax_data = json.dumps(tax_data)
            order.total_data = json.dumps(total_data)
            order.total_tax = json.dumps(total_tax)
            order.payment_method = request.POST['payment_method']
            #first let order.id generated
            order.save()
            order.order_number = generate_order_number(order.id)
            order.vendors.add(*vendors_ids)
            order.save()

            #Worldline Payment
            # client = Factory.create_client_from_file("payments_sdk.prp",
            #                                          W_API_KEY_ID,
            #                                          W_SECRET_API_KEY)
            # order_dict = {
            #     "order": {"amountOfMoney": {"currencyCode": "EUR", "amount": float(order.total)}},
            #     "payment method": {"card": order.payment_method},
            #     "receipt": "receipt #" + order.order_number,
            # }
            # print(client.merchant(MERCHANT_ID))
            #Klarna Payment


            context = {
                'order': order,
                'cart_items': cart_items,
                'KLARNA_MID': KLARNA_MID,
            }
            return render(request, 'orders/place_order.html', context)
        else:
            print(form.errors)
    return render(request, 'orders/place_order.html')

@login_required(login_url='login')
def payments(request):
    #Check if the request is ajax or not
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
    #STORE THE PAYMENT DETAILS IN THE PAYMENT MODEL
        order_number = request.POST.get('order_number')
        transaction_id = request.POST.get('transaction_id')
        payment_method = request.POST.get('payment_method')
        status = request.POST.get('status')

        order = Order.objects.get(user=request.user, order_number=order_number)
        payment = Payment(
            user=request.user,
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=order.total,
            status=status,
        )
        payment.save()
    #UPDATE THE ORDER MODEL
    order.payment = payment
    order.is_ordered = True
    order.save()
    #return HttpResponse('Saved!')

    #MOVE THE CARD ITEMS TO ORDERD FOOD MODEL
    cart_items = Cart.objects.filter(user=request.user)
    for item in cart_items:
        ordered_food = OrderedFood()
        ordered_food.order = order
        ordered_food.payment = payment
        ordered_food.user = request.user
        ordered_food.fooditem = item.fooditem
        ordered_food.quantity = item.quantity
        ordered_food.price = item.fooditem.price
        ordered_food.amount = item.fooditem.price * item.quantity
        ordered_food.save()
    #return HttpResponse('saved ordered food')

    #SEND ORDER CONFIRMATION EMAIL TO THE CUSTOMER
    mail_subject = 'Bedankt voor het bestellen bij ons.'
    mail_template = 'orders/order_confirmation_email.html'
    ordered_food = OrderedFood.objects.filter(order=order)
    customer_subtotal = 0

    for item in ordered_food:
        customer_subtotal += (item.price * item.quantity)
    tax_data = json.loads(order.tax_data)
    context = {
        'user': request.user,
        'order': order,
        'to_email': order.email,
        'ordered_food': ordered_food,
        'domain': get_current_site(request),
        'customer_subtotal': customer_subtotal,
        'tax_data': tax_data,
    }
    send_notification(mail_subject, mail_template, context)
    #return HttpResponse('Data saved and email sent')

    #SEND ORDER RECEIVED EMAIL TO THE VENDOR
    mail_subject = 'U hebt een nieuwe bestelling ontvangen.'
    mail_template = 'orders/new_order_received.html'
    to_emails = []
    for i in cart_items:
        if i.fooditem.vendor.user.email not in to_emails:
            to_emails.append(i.fooditem.vendor.user.email)

            ordered_food_to_vendor = OrderedFood.objects.filter(order=order, fooditem__vendor=i.fooditem.vendor)
            print(ordered_food_to_vendor)
       # print('to_emails=>', to_emails)
        context = {
            'order': order,
            'to_email': to_emails,
            'ordered_food_to_vendor': ordered_food_to_vendor,
            'vendor_subtotal': order_total_by_vendor(order, i.fooditem.vendor.id)['subtotal'],
            'tax_data': order_total_by_vendor(order, i.fooditem.vendor.id)['tax'],
            'vendor_grand_total': order_total_by_vendor(order, i.fooditem.vendor.id)['grand_total'],
         }
        send_notification(mail_subject, mail_template, context)

    #CLEAR THE CART IF THE PAYMENT IS SUCCESS
    #cart_items.delete()

    #RETURN BACK TO AJAX WITH STATUS SUCCESS OR FAILURE
        response = {
            'order_number': order_number,
            'transaction_id': transaction_id,
        }
        return JsonResponse(response)
    return HttpResponse('Payments views')

def order_complete(request):
    order_number = request.GET.get('order_no')
    transaction_id = request.GET.get('trans_id')

    try:
        order = Order.objects.get(order_number=order_number, payment__transaction_id=transaction_id, is_ordered=True)
        ordered_food = OrderedFood.objects.filter(order=order)

        subtotal = 0
        for item in ordered_food:
            subtotal += (item.price * item.quantity)

        tax_data = json.loads(order.tax_data)
        context = {
            'order': order,
            'ordered_food': ordered_food,
            'tax_data': tax_data,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except:
        return redirect('home')



