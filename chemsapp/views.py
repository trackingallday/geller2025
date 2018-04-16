from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from chemsapp.serializers import ProductSerializer, CustomerSerializer, SafetyWearSerializer, \
    ProductMapSerializer, UserSerializer, CustomerSheetSerializer, DistributorSerializer, PublicProductSerializer, \
    CategorySerializer, PostSererializer, MarketSerializer, ConfigSerializer, ContactSerializer, SizeSerializer
from chemsapp.models import Customer, Product, SafetyWear, Distributor, ProductCategory, Post, MarketCategory, Config, Contact, Size
from django.contrib.auth.models import User
from rest_framework.decorators import api_view,  authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

import base64
from django.core.files.base import ContentFile
import datetime
from django.db.models import Q
from django.core import serializers
import json
from django.core.mail import send_mail
import time


def getFileFromBase64(data, filename):
    format, imgstr = data.split(';base64,')
    ext = format.split('/')[-1]
    fname = filename + '.' + ext
    fileFieldData = ContentFile(base64.b64decode(imgstr), name=fname)
    return fileFieldData


def addInfoSheetToProduct(product, data):
    if not data:
        return product
    name = "{0}_{1}_{2}".format(product.id, product.name, 'info_sheet')
    sheet = getFileFromBase64(data, name)
    product.infoSheet = sheet
    return product


def addSDSSheetToProduct(product, data):
    if not data:
        return product
    name = "{0}_{1}_{2}".format(product.id, product.name, 'sds_sheet')
    sheet = getFileFromBase64(data, name)
    product.sdsSheet = sheet
    return product

def createImage(img_data):
    if not img_data:
	    return None
    name = str(time.time())
    return getFileFromBase64(img_data, name)


def create_user(data):
    user = User.objects.create_user(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        username=data['email'],
    )
    user.set_password(data['password'])
    user.save()
    return user


@csrf_exempt
def index(request):
    with open(os.path.join(settings.REACT_APP_DIR, 'build', 'index.html')) as f:
        return HttpResponse(f.read())

@csrf_exempt
def marketing_site(request):
    print(os.path.join(settings.MARKETING_APP_DIR, 'build', 'index.html'))
    with open(os.path.join(settings.MARKETING_APP_DIR, 'build', 'index.html')) as f:
        return HttpResponse(f.read())


@csrf_exempt
@api_view(['GET'])
def customers_list(request):
    if request.user.profile.profileType == 'admin':
        custs = CustomerSerializer(Customer.objects.all(), many=True).data
        return JsonResponse(custs, safe=False)

    customers = request.user.profile.distributor.customers
    serializer = CustomerSerializer(customers, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['GET'])
def products_list(request):
    if not request.user.profile.profileType == 'customer':
        products = Product.objects.all()
    else:
        products = request.user.profile.customer.products

    serializer = ProductSerializer(products, many=True, context={"user": request.user})
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['POST'])
def new_customer(request):
    proType = request.user.profile.profileType
    if proType not in ["distributor", "admin"]:
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']
    try:
        user = create_user(data)
    except Exception as e:
        return JsonResponse({'error': str(e)})

    customer = Customer.objects.create(
        user=user,
        phoneNumber=data.get('phoneNumber'),
        cellPhoneNumber=data.get('cellPhoneNumber'),
        businessName=data.get('businessName'),
        profileType=data.get('customer'),
        geocodingDetail=data.get('geocodingDetail'),
        address=data.get('address'),
    )

    customer.save()

    products = Product.objects.filter(pk__in=data.get('products'))
    customer.products = products
    customer.created_at = datetime.datetime.now()
    customer.distributorParent = request.user.profile.distributor
    customer.profileType = "customer"
    customer.save()
    request.user.profile.distributor.customers.add(customer)

    return JsonResponse({"message": "customer saved"})


@csrf_exempt
@api_view(['POST'])
def edit_customer(request):
    proType = request.user.profile.profileType
    if proType not in ["distributor", "admin"]:
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']
    customer = None
    if proType == 'admin':
        customer = Customer.objects.get(pk=data.get('id'))
    else:
        customer = request.user.profile.distributor.customers.get(id=data.get('id'))

    if not customer:
        return JsonResponse({"error": "evildoer"})

    customer.user.first_name = data.get('first_name')
    customer.user.last_name = data.get('last_name')
    customer.user.email = data.get('email')
    customer.user.save()

    customer.address = data.get('address')
    customer.businessName = data.get('businessName')
    customer.phoneNumber = data.get('phoneNumber')
    customer.cellPhoneNumber = data.get('cellPhoneNumber')

    if data.get('geocodingDetail'):
        customer.geocodingDetail = data.get('geocodingDetail')

    ids = [b for b in data.get('products') if isinstance(b, int)]
    names = [b.strip() for b in data.get('products') if isinstance(b, str)]

    my_filter = {'name__in': names}
    products = Product.objects.filter(Q(pk__in=ids) | Q(**my_filter))
    customer.products = products
    customer.updated_at = datetime.datetime.now()
    customer.save()

    return JsonResponse({"message": "customer edited"})


@csrf_exempt
@api_view(['POST'])
def new_distributor(request):
    proType = request.user.profile.profileType
    if not proType == "admin":
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']
    try:
        user = create_user(data)
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)})

    print(data.get('primaryImageLink'))
    distributor = Distributor.objects.create(
        user=user,
        phoneNumber=data.get('phoneNumber'),
        cellPhoneNumber=data.get('cellPhoneNumber'),
        businessName=data.get('businessName'),
        profileType=data.get('customer'),
        geocodingDetail=data.get('geocodingDetail'),
        address=data.get('address'),
        primaryImageLink=createImage(data.get('primaryImageLink')),
    )

    user.save()
    distributor.user = user
    distributor.customers = []
    distributor.profileType = 'distributor'
    distributor.created_at = datetime.datetime.now()
    distributor.save()

    return JsonResponse({"message": "distributor saved"})


@csrf_exempt
@api_view(['POST'])
def edit_distributor(request):
    proType = request.user.profile.profileType
    if not proType == "admin":
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']

    distributor = Distributor.objects.get(id=data.get('id'))
    if not distributor:
        return JsonResponse({"error": "evildoer"})

    distributor.user.first_name = data.get('first_name')
    distributor.user.last_name = data.get('last_name')
    distributor.user.email = data.get('email')

    distributor.user.save()

    distributor.address = data.get('address')
    distributor.businessName = data.get('businessName')
    distributor.phoneNumber = data.get('phoneNumber')
    distributor.cellPhoneNumber = data.get('cellPhoneNumber')

    if data.get('geocodingDetail'):
        distributor.geocodingDetail = data.get('geocodingDetail')

    if data.get('primaryImageLink'):
        distributor.primaryImageLink = createImage(data.get('primaryImageLink'))

    distributor.save()

    return JsonResponse({"message": "distributor edited"})



@csrf_exempt
@api_view(['GET'])
def safety_wears_list(request):
    serializer = SafetyWearSerializer(SafetyWear.objects.all(), many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['POST'])
def new_product(request):
    proType = request.user.profile.profileType
    if proType not in ["distributor", "admin"]:
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']
    product = Product.objects.create(
        name=data.get('name'),
        usageType=data.get('usageType'),
        amountDesc=data.get('amountDesc'),
        instructions=data.get('instructions'),
        productCode=data.get('productCode'),
        brand=data.get('brand'),
        properties=data.get('properties'),
        application=data.get('application'),
        description=data.get('description'),
        subCategory=data.get('subCategory'),
        uploadedBy=request.user,
    )
    product.save()
    product.primaryImageLink=createImage(data.get('primaryImageLink'))
    product.secondaryImageLink=createImage(data.get('secondaryImageLink'))

    product = addInfoSheetToProduct(product, data.get('infoSheet'))
    product = addSDSSheetToProduct(product, data.get('sdsSheet'))
    product.safetyWears = SafetyWear.objects.filter(pk__in=data.get('safetyWears'))
    product.markets = MarketCategory.objects.filter(pk__in=data.get('markets'))
    product.sizes = Size.objects.filter(pk__in=data.get('sizes'))

    if data.get('productCategory'):
        product.productCategory = ProductCategory.objects.filter(pk__in=data.get('productCategory'))
    product.updated_at = datetime.datetime.now()
    product.save()

    return JsonResponse({"message": "product saved"})


@csrf_exempt
@api_view(['POST'])
def edit_product(request):
    proType = request.user.profile.profileType
    if proType not in ["distributor", "admin"]:
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']
    product = Product.objects.get(id=data.get('id'))

    if not product:
        return JsonResponse({"error": "evildoer"})

    product.safetyWears = SafetyWear.objects.filter(pk__in=data.get('safetyWears'))
    product.name = data.get('name')
    product.usageType = data.get('usageType')
    product.amountDesc = data.get('amountDesc')
    product.instructions = data.get('instructions')
    product.productCode = data.get('productCode')
    product.brand = data.get('brand')
    product.properties = data.get('properties')
    product.application = data.get('application')
    product.description = data.get('description')
    product.subCategory = data.get('subCategory')
    product.markets = MarketCategory.objects.filter(pk__in=data.get('markets'))
    if data.get('productCategory'):
        product.productCategory = ProductCategory.objects.filter(pk__in=data.get('productCategory'))
    if data.get('sizes'):
        product.sizes = Size.objects.filter(pk__in=data.get('sizes'))
    print(data.get('sizes'))
    product.updated_at = datetime.datetime.now()

    if data.get('secondaryImageLink'):
        product.secondaryImageLink=createImage(data.get('secondaryImageLink'))

    if data.get('primaryImageLink'):
        product.primaryImageLink=createImage(data.get('primaryImageLink'))

    if data.get('sdsSheet'):
        product = addSDSSheetToProduct(product, data.get('sdsSheet'))

    if data.get('infoSheet'):
        product = addInfoSheetToProduct(product, data.get('infoSheet'))

    product.updated_at = datetime.datetime.now()

    product.save()

    return JsonResponse({"message": "product edited"})


@csrf_exempt
@api_view(['POST', 'GET'])
def user_details(request):
    data = UserSerializer(request.user).data
    data['emails'] = [u.email for u in User.objects.all()]
    return JsonResponse(data)


@csrf_exempt
@api_view(['GET'])
def products_map(request):
    if not request.user.profile.profileType == "admin":
        return JsonResponse({"error": "evildoer"})

    products = Product.objects.all()
    return JsonResponse(ProductMapSerializer(products, many=True).data, safe=False)


@csrf_exempt
@api_view(['GET'])
def customers_table_admin(request):
    if request.user.profile.profileType == 'admin':
        products = Product.objects.only('id', 'name')
        customers = CustomerSerializer(Customer.objects.all(), many=True).data
        return JsonResponse({"customers": customers, "products": products})
    else:
        return JsonResponse({"error": "evildoer"})


@csrf_exempt
@api_view(['GET'])
def customers_table(request):
    profile = request.user.profile
    if profile.profileType == "distributor":
        products = profile.distributor.products.only('id', 'name')
        customers = CustomerSerializer(profile.distributor.customers, many=True).data
        return JsonResponse({"customers": customers, "products": products})

    return JsonResponse({"error": "evildoer"})


@csrf_exempt
@api_view(['POST', 'GET'])
def printout(request):
    if request.method == 'POST':
        data = request.data['data']
        if request.user.profile.profileType == 'admin':
            customer = Customer.objects.get(pk=int(data['customer_id']))
        else:
            customer = request.user.profile.distributor.customers.get(pk=int(data['customer_id']))
        if not customer:
            return JsonResponse({'error': 'evildoer'})

        cust = CustomerSheetSerializer(customer, many=False).data
    else:
        cust = CustomerSheetSerializer(request.user.profile.customer, many=False).data

    return JsonResponse(cust)


@csrf_exempt
@api_view(['GET'])
def distributors_list(request):
    if request.user.profile.profileType == 'admin':
        data = DistributorSerializer(Distributor.objects.all(), many=True).data
        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'evildoer'})

@csrf_exempt
def public_products(request):
    try:
        products = PublicProductSerializer(Product.objects.all(), many=True).data
        categories = CategorySerializer(ProductCategory.objects.all(), many=True).data
        posts = PostSererializer(Post.objects.all(), many=True).data
        markets = MarketSerializer(MarketCategory.objects.all(), many=True).data
        configs = ConfigSerializer(Config.objects.all(), many=True).data
        sizes = SizeSerializer(Size.objects.all(), many=True).data
        return JsonResponse(
            {'products': products, 'categories': categories, 'posts': posts,
             'markets': markets, 'configs': configs, 'sizes': sizes}, safe=False)
    except Exception as a:
        print(a)
    pass


@csrf_exempt
@api_view(['GET'])
def markets_list(request):
    if request.user:
        data = MarketSerializer(MarketCategory.objects.all(), many=True).data
        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'evildoer'})

@csrf_exempt
@api_view(['GET'])
def categories_list(request):
    if request.user:
        data = CategorySerializer(ProductCategory.objects.all(), many=True).data
        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'evildoer'})


@csrf_exempt
@api_view(['GET'])
def sizes_list(request):
    if request.user:
        data = SizeSerializer(Size.objects.all(), many=True).data
        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'evildoer'})


@csrf_exempt
def create_contact(request):
    try:
        b = json.loads(request.GET['data'])
        c = ContactSerializer(data=b)
        c.is_valid()
        a = c.validated_data
        c.create(a)
        send_mail(
            'Contact from Geller.co.nz',
            b['nameFrom'] + ' ' + b['emailFrom'] + ' ' + b['content'],
            'chemicaldatasheets@gmail.com',
            ['james@integraindustries.co.nz'],
            fail_silently=False,
        )
        send_mail(
            'Contact from Geller.co.nz',
            'Hi ' + b['nameFrom'] + ' Thanks for you contact request we will be in touch shortly.',
            'chemicaldatasheets@gmail.com',
            [b['emailFrom'], 'james@integraindustries.co.nz'],
            fail_silently=False,
        )
        return JsonResponse({'sddsfds':'sdfsefsfseffse'})
    except Exception as e:
        print("ERROR")
        print(e)
