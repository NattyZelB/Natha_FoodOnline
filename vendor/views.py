from django.shortcuts import render

def vProfile(request):
    return render(request, 'vendor/vProfile.html')
