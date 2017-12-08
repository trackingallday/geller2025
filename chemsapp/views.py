from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from chemsapp.serializers import ProductSerializer, CustomerSerializer
from chemsapp.models import Customer, Product
from django.contrib.auth.models import User
from rest_framework.decorators import api_view


@csrf_exempt
@login_required
def index(request):
    with open(os.path.join(settings.REACT_APP_DIR, 'build', 'index.html')) as f:
        return HttpResponse(f.read())


@csrf_exempt
@api_view(['GET'])
def customers_list(request):
    customers = request.user.profile.distributor.customers
    serializer = CustomerSerializer(customers, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['GET'])
def products_list(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['POST'])
def new_customer(request):
    if not request.user.profile.profileType == "distributor":
        return JsonResponse(False)
    user = User.objects.create_user(
        username=request.POST.get('username'),
        email=request.POST.get('email'),
        password=request.POST('password'),
    )

    customer = Customer.objects.create(
        user=user,
        phoneNumber=request.POST.get('phoneNumber'),
        cellPhoneNumber=request.POST.get('cellPhoneNumber'),
        businessName=request.POST.get('businessName'),
        lat=request.POST.get('lat'),
        lon=request.POST.get('lon'),
        profileType=request.POST.get('profileType'),
        products=[]
    )

    customer.save()
    return JsonResponse(True)
