from django.shortcuts import render, redirect
from .forms import UserForm
from .models import User, UserProfile
from vendor.forms import VendorForm
from django.contrib import messages, auth
from .utils import detectUser
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied


#restrict the vendor from accessing the vendor page
def check_role_vendor(user):
    if user.role == 1:
        return True
    else:
        raise PermissionDenied

#restrict the vendor from accessing the customer page
def check_role_customer(user):
    if user.role == 2:
        return True
    else:
        raise PermissionDenied

def registerUser(request):
    if request.user.is_authenticated:
        messages.warning(request, 'U bent al ingelogd.')
        return redirect('custDashboard')
    elif request.method == 'POST':
        print(request.POST)
        form = UserForm(request.POST)
        if form.is_valid():
            #Create the user using the form
            # password = form.cleaned_data['password']
            # user = form.save(commit=False)
            # #edit Invalid password format or unknown hashing algorithm.
            # user.set_password(password)
            # user.role =User.CUSTOMER
            # form.save()

            #Create the user using create_user method
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.role = user.CUSTOMER
            user.save()
            messages.success(request, 'Uw account is succesvol geregistreerd!')
            return redirect('registerUser')
        else:
            print('invalid form')
            print(form.errors)
    else:
        form = UserForm()
    context = {
        'form': form,
       }
    return render(request, 'accounts/registerUser.html', context)

def registerVendor(request):
    if request.user.is_authenticated:
        messages.warning(request, 'U bent al ingelogd.')
        return redirect('vendorDashboard')
    if request.method == 'POST':
       #store the data and create the user
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST, request.FILES)
        if form.is_valid() and v_form.is_valid():
           first_name = form.cleaned_data['first_name']
           last_name = form.cleaned_data['last_name']
           email = form.cleaned_data['email']
           username = form.cleaned_data['username']
           password = form.cleaned_data['password']
           user = User.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
           user.role = user.VENDOR
           user.save()
           vendor = v_form.save(commit=False)
           vendor.user =user
           user_profile = UserProfile.objects.get(user=user)
           vendor.user_profile = user_profile
           vendor.save()
           messages.success(request, 'Uw account is succesvol geregistreerd! Wacht op de goedkeuring.')
           return redirect('registerVendor')
        else:
           print('invalid form')
           print(form.errors)
    else:
        form = UserForm()
        v_form = VendorForm()
    context = {
        'form': form,
        'v_form': v_form,
    }
    return render(request, 'accounts/registerVendor.html', context)

def login (request):
    if request.user.is_authenticated:
        messages.warning(request, 'U bent al ingelogd.')
        return redirect('custDashboard')
    elif request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        #check authenticated
        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, 'U bent nu ingelogd.')
            return redirect('myAccount')
        else:
            messages.error(request, 'Ongeldige inloggegevens')
            return redirect('login')

    return render(request, 'accounts/login.html')

def logout(request):
    auth.logout(request)
    messages.info(request, 'U bent uitgelogd.')
    return redirect('login')

@login_required(login_url = 'login')
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)

    return redirect(redirectUrl)

@login_required(login_url = 'login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    return render(request, 'accounts/custDashboard.html')

@login_required(login_url = 'login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    return render(request, 'accounts/vendorDashboard.html')
