from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from chemsapp.serializers import ProductSerializer, CustomerSerializer, SafetyWearSerializer
from chemsapp.models import Customer, Product, SafetyWear
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
import json


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
        return JsonResponse({"message": "you cannot create customers"})

    data = request.data['data']
    user = User.objects.create_user(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password=['password'],
        username=data['email'],
    )

    customer = Customer.objects.create(
        user=user,
        phoneNumber=data.get('phoneNumber'),
        cellPhoneNumber=data.get('cellPhoneNumber'),
        businessName=data.get('businessName'),
        profileType=data.get('customer'),
        geocodingDetail=data.get('geocodingDetail'),
        address=data.get('address'),
    )

    products = Product.objects.filter(pk__in=data.get('products'))
    customer.products = products
    customer.save()
    request.user.profile.distributor.customers.add(customer)

    return JsonResponse({"message": "customer saved"})


@csrf_exempt
@api_view(['POST'])
def edit_customer(request):
    if not request.user.profile.profileType == "distributor":
        return JsonResponse({"message": "you cannot edit customers"})

    data = request.data['data']
    print(data)

    customer = request.user.profile.distributor.customers.get(id=data.get('id'))

    if not customer:
        return JsonResponse({"message": "you may not edit this customer"})

    customer.user.first_name = data.get('first_name')
    customer.user.last_name = data.get('last_name')
    customer.user.save()

    customer.address = data.get('address')
    customer.businessName = data.get('businessName')
    customer.phoneNumber = data.get('phoneNumber')
    customer.cellPhoneNumber = data.get('cellPhoneNumber')

    if data.get('geocodingDetail'):
        customer.geocodingDetail = data.get('geocodingDetail')

    customer.save()

    return JsonResponse({"message": "customer edited"})


@csrf_exempt
@api_view(['GET'])
def safety_wears_list(request):
    return JsonResponse(SafetyWearSerializer(SafetyWear.objects.all(), many=True))



