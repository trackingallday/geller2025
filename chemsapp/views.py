import logging
import random
import string
from django.forms import ValidationError
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
import os

import requests
from chemsapp.serializers import ProductSerializer, CustomerSerializer, SafetyWearSerializer, \
    ProductMapSerializer, UserSerializer, CustomerSheetSerializer, DistributorSerializer, PublicProductSerializer, \
    CategorySerializer, PostSererializer, MarketSerializer, ConfigSerializer, ContactSerializer, SizeSerializer
from chemsapp.models import Customer, Product, SafetyWear, Distributor, ProductCategory, Post, MarketCategory, Config, Contact, Size
from django.contrib.auth.models import User
from rest_framework.decorators import api_view

import base64
from django.core.files.base import ContentFile
import datetime
from django.db.models import Q
from django.core import serializers
import json
from django.core.mail import EmailMessage
import time

logger = logging.getLogger('django')

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
    if not img_data or not ';base64,' in img_data:
        return None
    name = str(time.time())
    return getFileFromBase64(img_data, name)


def create_user(data):
    user = User.objects.create_user(
        first_name=data.get('first_name'),
        last_name=data.get('last_name', ''),
        email=data.get('email'),
        username=data.get('email'),
    )
    user.set_password(''.join(random.choice(string.ascii_letters) for i in range(10)))
    user.save()
    return user

def mail_admin(subject, content, reply_to=None):
    msg = EmailMessage(
        subject=subject,
        body=content,
        from_email=settings.EMAIL_FROM,
        to=[settings.EMAIL_ADMIN],
        reply_to=[reply_to or settings.EMAIL_ADMIN]
    )
    return msg.send()

def mail_customer(subject, content, customer_email, reply_to=None):
    msg = EmailMessage(
        subject=subject,
        body=content,
        from_email=settings.EMAIL_FROM,
        to=[customer_email],
        reply_to=[reply_to or settings.EMAIL_ADMIN]
    )
    return msg.send()


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


@transaction.atomic
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
        return JsonResponse({'error': str(e)}, status=422)

    try:
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
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=422)

    products = Product.objects.filter(pk__in=data.get('products'))
    customer.products = products
    customer.created_at = datetime.datetime.now()
    customer.distributorParent = request.user.profile.distributor
    customer.profileType = "customer"
    customer.save()
    request.user.profile.distributor.customers.add(customer)

    return JsonResponse({"message": "customer saved"})


@transaction.atomic
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

    products = Product.objects.filter(Q(pk__in=ids) | Q(name__in=names))

    customer.products = products
    customer.updated_at = datetime.datetime.now()
    customer.save()

    return JsonResponse({"message": "customer edited"})


@transaction.atomic
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
        return JsonResponse({'error': str(e)}, status=422)

    try:
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
        distributor.save()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=422)

    user.save()
    distributor.user = user
    distributor.customers = []
    distributor.profileType = 'distributor'
    distributor.created_at = datetime.datetime.now()
    distributor.save()

    return JsonResponse({"message": "distributor saved"})


@transaction.atomic
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

    if data.get('primaryImageLink') and not distributor.primaryImageLink == data.get('primaryImageLink'):
        distributor.primaryImageLink = createImage(data.get('primaryImageLink'))

    distributor.save()

    return JsonResponse({"message": "distributor edited"})



@csrf_exempt
@api_view(['GET'])
def safety_wears_list(request):
    serializer = SafetyWearSerializer(SafetyWear.objects.all(), many=True)
    return JsonResponse(serializer.data, safe=False)


@transaction.atomic
@csrf_exempt
@api_view(['POST'])
def new_product(request):
    proType = request.user.profile.profileType
    if proType not in ["distributor", "admin"]:
        return JsonResponse({"error": "evildoer"})

    data = request.data['data']
    try:
        product = Product.objects.create(
            name=data.get('name'),
            usageType=data.get('usageType'),
            amountDesc=data.get('amountDesc'),
            directions=data.get('directions'),
            productCode=data.get('productCode'),
            brand=data.get('brand'),
            properties=data.get('properties'),
            application=data.get('application'),
            description=data.get('description'),
            uploadedBy=request.user,
        )
        product.save()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=422)

    product.primaryImageLink=createImage(data.get('primaryImageLink'))
    product.secondaryImageLink=createImage(data.get('secondaryImageLink'))

    product = addInfoSheetToProduct(product, data.get('infoSheet'))
    product = addSDSSheetToProduct(product, data.get('sdsSheet'))
    product.safetyWears = SafetyWear.objects.filter(pk__in=data.get('safetyWears'))
    product.subCategory = ProductCategory.objects.filter(pk__in=data.get('subCategory'))
    product.markets = MarketCategory.objects.filter(pk__in=data.get('markets'))
    product.sizes = Size.objects.filter(pk__in=data.get('sizes'))

    for key in ['productCategory', 'subCategory']:
        if data.get(key):
            product.productCategory = ProductCategory.objects.filter(pk__in=data.get(key))

    product.updated_at = datetime.datetime.now()
    product.save()

    return JsonResponse({"message": "product saved"})


@transaction.atomic
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
    product.directions = data.get('directions')
    product.productCode = data.get('productCode')
    product.brand = data.get('brand')
    product.properties = data.get('properties')
    product.application = data.get('application')
    product.description = data.get('description')
    product.subCategory = data.get('subCategory')
    product.markets = MarketCategory.objects.filter(pk__in=data.get('markets'))

    for key in ['productCategory', 'subCategory']:
        if data.get(key):
            setattr(product, key, ProductCategory.objects.filter(pk__in=data.get(key)))

    if data.get('sizes'):
        product.sizes = Size.objects.filter(pk__in=data.get('sizes'))
    print(data.get('sizes'))
    product.updated_at = datetime.datetime.now()

    for key in ['primaryImageLink', 'secondaryImageLink']:
        if data.get(key) and not getattr(product, key) == data.get(key):
            setattr(product,key,createImage(data.get(key)))

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
        products = PublicProductSerializer(Product.objects.filter(public=True), many=True).data
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
    b = json.loads(request.GET['data'])

    cap_value = b.pop("captcha_token")
    r = requests.post('https://www.google.com/recaptcha/api/siteverify',
                        { 'secret': settings.RECAPTCHA_PRIVATE_KEY, 'response': cap_value })
    res = r.json()
    if not res.get('success') or res.get('score', 0) < 0.7:
        raise ValidationError('There was a problem with your request, please try again', code="recaptcha")

    c = ContactSerializer(data=b)
    c.is_valid()
    a = c.validated_data
    c.create(a)
    mail_admin('Contact from Geller.co.nz',
        b['nameFrom'] + '\n' + b['emailFrom'] + '\nMessage:\n' + b['content'],
        reply_to=b['emailFrom']
    )
    mail_customer('Contact from Geller.co.nz',
        'Hi ' + b['nameFrom'] + ',\n\nThanks for you contact request we will be in touch shortly.',
        b['emailFrom']
    )

    # Return response even if there is an error. 
    return JsonResponse({'sddsfds':'sdfsefsfseffse'})

@csrf_exempt
def sds_enquire(request):
    try:
        b = json.loads(request.GET['data'])
        b['isSDSDownload'] = True

        # Resolve product name
        product = Product.objects.get(id=b['productId'])
        productName = "Error: Unknown Product ({})".format(b['productId'])
        if product:
            productName = product.name
        b['productName'] = productName
        b['content'] = 'Downloaded SDS for product:' + productName

        c = ContactSerializer(data=b)
        c.is_valid()

        a = c.validated_data
        c.create(a)

        mail_admin(
            'Contact from Geller.co.nz',
            """A customer has downloaded an SDS for a product.
Name: {nameFrom}
Company: {companyName}
Email: {emailFrom}
Product: {productName}""".format(**b),
        )
    except Exception as e:
        # Dump the error into alllogs.log
        logger.error(e)

    # Return response even if there is an error. 
    return JsonResponse({'sddsfds':'sdfsefsfseffse'})


def _download_pdf_document(file_path, preferred_name=None):
    if preferred_name is None:
        preferred_name = os.path.basename(file_path)
    try:
        with open(file_path, 'rb') as document:
            response = HttpResponse(document.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(preferred_name)
            return response
    except Exception as e:
        print("ERROR")
        print(e)
        raise Http404("Document was not found.")


@csrf_exempt
def download_product_document(request, product_id, document_type):
    try:
        if document_type not in ['sds', 'info']:
            raise Http404("Document was not found.")
        product = Product.objects.get(id=product_id)
        if not product:
            raise Http404("Product was not found.")
        if 'sds' == document_type and product.sdsSheet and product.sdsSheet.path.strip():
            return _download_pdf_document(product.sdsSheet.path)
        if 'info' == document_type and product.infoSheet and product.infoSheet.path.strip():
            return _download_pdf_document(product.infoSheet.path)
        raise Http404("Document was not found.")
    except Http404:
        raise
    except Exception as e:
        # Dump the error into alllogs.log
        logger.error(e)
        raise Http404("Document was not found.")