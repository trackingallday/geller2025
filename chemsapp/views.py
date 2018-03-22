from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from chemsapp.serializers import ProductSerializer, CustomerSerializer, SafetyWearSerializer, \
    ProductMapSerializer, UserSerializer, CustomerSheetSerializer, DistributorSerializer, PublicProductSerializer, \
    CategorySerializer, PostSererializer, MarketSerializer
from chemsapp.models import Customer, Product, SafetyWear, Distributor, ProductCategory, Post, MarketCategory
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
import base64
from django.core.files.base import ContentFile
import datetime
from django.db.models import Q
from django.core import serializers


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
        return JsonResponse({'error': str(e)})

    distributor = Distributor.objects.create(
        user=user,
        phoneNumber=data.get('phoneNumber'),
        cellPhoneNumber=data.get('cellPhoneNumber'),
        businessName=data.get('businessName'),
        profileType=data.get('customer'),
        geocodingDetail=data.get('geocodingDetail'),
        address=data.get('address'),
        primaryImageLink=data.get('primaryImageLink'),
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
        distributor.primaryImageLink = data.get('primaryImageLink')

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
        primaryImageLink=data.get('primaryImageLink'),
        secondaryImageLink=data.get('secondaryImageLink'),
        usageType=data.get('usageType'),
        amountDesc=data.get('amountDesc'),
        instructions=data.get('instructions'),
        productCode=data.get('productCode'),
        brand=data.get('brand'),
        properties=data.get('properties'),
        application=data.get('application'),
        uploadedBy=request.user,
    )
    product.save()

    product = addInfoSheetToProduct(product, data.get('infoSheet'))
    product = addSDSSheetToProduct(product, data.get('sdsSheet'))
    product.safetyWears = SafetyWear.objects.filter(pk__in=data.get('safetyWears'))
    product.markets = MarketCategory.objects.filter(pk__in=data.get('markets'))
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
    product.markets = MarketCategory.objects.filter(pk__in=data.get('markets'))
    product.updated_at = datetime.datetime.now()

    if data.get('secondaryImageLink'):
        product.secondaryImageLink = data.get('secondaryImageLink')

    if data.get('primaryImageLink'):
        product.primaryImageLink = data.get('primaryImageLink')

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
        return JsonResponse({'products': products, 'categories': categories, 'posts': posts, 'markets': markets}, safe=False)
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
