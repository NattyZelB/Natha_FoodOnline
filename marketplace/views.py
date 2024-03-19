from django.shortcuts import render, get_object_or_404, redirect
from vendor.models import Vendor
from menu.models import Category, FoodItem
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from .models import Cart
from marketplace.context_processors import get_cart_counter, get_cart_amounts
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from vendor.views import OpeningHour
from datetime import date, datetime
from orders.forms import OrderForm
from accounts.models import UserProfile
def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()
    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
    }
    return render(request, 'marketplace/listings.html', context)

def vendor_detail(request, vendor_slug):
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    #prefech_related เอาไว้เชื่อม model กับ model
    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch(
            'fooditems',
            queryset = FoodItem.objects.filter(is_available=True)
        )
    )
    opening_hours = OpeningHour.objects.filter(vendor=vendor).order_by('day', '-from_hour')
    # Check current day's opening hours.
    today_date = date.today()
    #isoweekday return no. from day
    today = today_date.isoweekday()
    current_opening_hours = OpeningHour.objects.filter(vendor=vendor, day=today)

    #print(type(current_time))


    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        cart_items = None
    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
        'opening_hours': opening_hours,
        'current_opening_hours': current_opening_hours,
    }
    return render(request, 'marketplace/vendor_detail.html', context)

def add_to_cart(request,food_id):

    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Check if it is ajax request
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added the item to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    # Increase cart quantity
                    chkCart.quantity += 1
                    chkCart.save()
                    return JsonResponse({'satus': 'success', 'message': 'Het aantal winkelwagens verhoogd', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity, 'cart_amount': get_cart_amounts(request)})
                except:
                    chkCart = Cart.objects.create(user=request.user, fooditem=fooditem, quantity=1)
                    return JsonResponse({'satus': 'success', 'message': 'Het artikel aan de winkelwagen toegevoegd', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity, 'cart_amount': get_cart_amounts(request)})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'Dit eten bestaat niet!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Ongeldig verzoek!'})
    else:
        return JsonResponse({'status': 'Login required', 'message': 'Gelieve in te loggen om door te gaan.'})

def decrease_cart(request,food_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Check if it is ajax request
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added the item to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user, fooditem=fooditem)
                    if chkCart.quantity >= 1:
                        # Decrease cart quantity
                        chkCart.quantity -= 1
                        chkCart.save()
                    else:
                        chkCart.delete()
                        chkCart.quantity = 0
                    return JsonResponse({'satus': 'Success', 'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity, 'cart_amount': get_cart_amounts(request)})
                except:
                    return JsonResponse({'status': 'Failed', 'message': 'U heeft dit artikel niet in uw winkelwagen!'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'Dit eten bestaat niet!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Ongeldig verzoek!'})
    else:
        return JsonResponse({'status': 'Login  required', 'message': 'Gelieve in te loggen om door te gaan.'})

@login_required(login_url = 'login')
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/cart.html', context)

def delete_cart(request, cart_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                #check if the cart item exists
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                if cart_item:
                    cart_item.delete()
                    return JsonResponse({'status': 'Success', 'message': 'Winkelwagenitem is verwijderd!', 'cart_counter': get_cart_counter(request), 'cart_amount': get_cart_amounts(request)})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'Dit eten bestaat niet!'})

        else:
            return JsonResponse({'status': 'Failed', 'message': 'Ongeldig verzoek!'})

def search(request):
    if not 'address' in request.GET:
        return redirect('marketplace')
    else:
        address = request.GET['address']
        latitude = request.GET['lat']
        longitude = request.GET['lng']
        radius = request.GET['radius']
        keyword = request.GET['keyword']

        fetch_vendors_by_fooditems = FoodItem.objects.filter(food_title__icontains=keyword, is_available=True).values_list('vendor', flat=True)
        vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_fooditems) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True))
        if latitude and longitude and radius:
            pnt = GEOSGeometry('POINT(%s %s)' % (longitude, latitude))
            vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_fooditems) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True),
                                            user_profile__location__distance_lte=(pnt, D(km=radius))).annotate(
                                            distance=Distance("user_profile__location", pnt)).order_by('distance')

            for v in vendors:
                v.kms = round(v.distance.km, 1)

        vendor_count = vendors.count()

        # get vendor id's that has the food item the user is looking for

        context = {
            'vendors': vendors,
            'vendor_count': vendor_count,
            'source_location': address,
         }
        return render(request, 'marketplace/listings.html', context)
@login_required(login_url='login')
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')

    user_profile = UserProfile.objects.get(user=request.user)
    default_values = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'phone': request.user.phone_number,
        'GSM': request.user.GSM,
        'email': request.user.email,
        'address': user_profile.address,
        'huis_number': user_profile.huis_number,
        'bus_number': user_profile.bus_number,
        'city': user_profile.city,
        'country': user_profile.country,
        'pin_code': user_profile.pin_code,
    }
    form = OrderForm(initial=default_values)
    context = {
        'form': form,
        'cart_items': cart_items,
        #'cart_count': cart_count,
    }
    return render(request, 'marketplace/checkout.html', context)
