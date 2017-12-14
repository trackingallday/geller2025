from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from chemsapp.serializers import ProductSerializer, CustomerSerializer, SafetyWearSerializer, UserSerializer
from chemsapp.models import Customer, Product, SafetyWear
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
import base64
from django.core.files.base import ContentFile
import datetime


def getFileFromBase64(data, filename):
    format, imgstr = data.split(';base64,')
    ext = format.split('/')[-1]
    fname = filename + '.' + ext
    fileFieldData = ContentFile(base64.b64decode(imgstr), name=fname)
    return fileFieldData


def addInfoSheetToProduct(product, data):
    name = "{0}_{1}_{2}".format(product.id, product.name, 'info_sheet')
    sheet = getFileFromBase64(data, name)
    product.infoSheet = sheet
    return product


def addSDSSheetToProduct(product, data):
    name = "{0}_{1}_{2}".format(product.id, product.name, 'sds_sheet')
    sheet = getFileFromBase64(data, name)
    product.sdsSheet = sheet
    return product


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
    products = []

    if not request.user.profile.customer:
        products = Product.objects.all()
    else:
        products = request.user.profile.customer.products

    serializer = ProductSerializer(products, many=True, context={"user": request.user})
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['POST'])
def new_customer(request):
    if not request.user.profile.profileType == "distributor":
        return JsonResponse({"error": "evildoer"})

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
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']

    customer = request.user.profile.distributor.customers.get(id=data.get('id'))

    if not customer:
        return JsonResponse({"error": "evildoer"})

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
    serializer = SafetyWearSerializer(SafetyWear.objects.all(), many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['POST'])
def new_product(request):
    if not request.user.profile.profileType == "distributor":
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']
    product = Product.objects.create(
        name=data.get('name'),
        primaryImageLink=data.get('primaryImageLink'),
        secondaryImageLink=data.get('secondaryImageLink'),
        usageType=data.get('usageType'),
        amountDesc=data.get('amountDesc'),
        instructions=data.get('instructions'),
        productCode=data.get('productCode'),
        brand=data.get('brand'),
        uploadedBy=request.user,
    )
    product.save()

    product = addInfoSheetToProduct(product, data.get('infoSheet'))
    product = addSDSSheetToProduct(product, data.get('sdsSheet'))
    product.safetyWears = SafetyWear.objects.filter(pk__in=data.get('safetyWears'))
    product.save()

    return JsonResponse({"message": "product saved"})


@csrf_exempt
@api_view(['POST'])
def edit_product(request):
    if not request.user.profile.profileType == "distributor":
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']
    product = Product.objects.get(id=data.get('id'))

    if not product:
        return JsonResponse({"error": "evildoer"})

    product.safetyWears = SafetyWear.objects.filter(pk__in=data.get('safetyWears'))
    product.name = data.get('name')
    product.primaryImageLink = data.get('primaryImageLink')
    product.secondaryImageLink = data.get('secondaryImageLink')
    product.usageType = data.get('usageType')
    product.amountDesc = data.get('amountDesc')
    product.instructions = data.get('instructions')
    product.productCode = data.get('productCode')
    product.brand = data.get('brand')
    product.updated_at = datetime.datetime.now

    if data.get('sdsSheet'):
        product = addSDSSheetToProduct(product, data.get('sdsSheet'))

    if data.get('infoSheet'):
        product = addInfoSheetToProduct(product, data.get('infoSheet'))

    product.save()

    return JsonResponse({"message": "customer edited"})


@csrf_exempt
@api_view(['POST', 'GET'])
def user_details(request):
    data = UserSerializer(request.user).data
    print(data)
    return JsonResponse(data)






