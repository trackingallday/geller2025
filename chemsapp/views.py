import logging
import random
import string
from django.views.decorators.cache import cache_control
from django.forms import ValidationError
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse, Http404
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
import os
import threading
from PIL import Image, ImageCms
import io

MAX_DIM = 1200
JPEG_QUALITY = 80


def _prepare_image(img, fmt):
    """
    Convert color mode to RGB if needed and downscale to fit MAX_DIM.
    Uses ICC profile for accurate CMYK-to-RGB conversion when available.
    Returns (img, changed) where changed is True if the image was modified.
    """
    changed = False

    if img.mode == 'CMYK':
        icc_profile = img.info.get('icc_profile')
        if icc_profile:
            src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc_profile))
            dst_profile = ImageCms.createProfile('sRGB')
            img = ImageCms.profileToProfile(img, src_profile, dst_profile, outputMode='RGB')
        else:
            img = img.convert('RGB')
        changed = True
    elif fmt == 'JPEG' and img.mode != 'RGB':
        img = img.convert('RGB')
        changed = True
    elif img.mode in ('P', 'LA', 'PA'):
        img = img.convert('RGBA' if fmt == 'PNG' else 'RGB')
        changed = True

    if img.width > MAX_DIM or img.height > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM), Image.BILINEAR)
        changed = True

    return img, changed


def downscale_image(file_path):
    """
    Resize image at file_path in-place to fit within MAX_DIM x MAX_DIM.
    Only processes JPEG and PNG files; skips everything else.
    Returns True if the file was changed, False otherwise.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in {'.jpg', '.jpeg', '.png'}:
        return False
    try:
        with Image.open(file_path) as img:
            orig_fmt = img.format  # 'JPEG', 'PNG', etc.
            img, changed = _prepare_image(img, orig_fmt)
            if not changed:
                return False

            save_kwargs = {}
            if orig_fmt == 'JPEG':
                save_kwargs = {'quality': JPEG_QUALITY, 'optimize': True}
            img.save(file_path, orig_fmt, **save_kwargs)
            return True

    except Exception:
        # Not an image or unreadable — leave it alone
        return False

import requests
from chemsapp.serializers import ProductSerializer, CustomerSerializer, SafetyWearSerializer, \
    ProductMapSerializer, UserSerializer, CustomerSheetSerializer, DistributorSerializer, PublicProductSerializer, \
    CategorySerializer, PostSererializer, MarketSerializer, ConfigSerializer, ContactSerializer, SizeSerializer, \
    SectorSerializer, NewsPostSerializer
from chemsapp.models import Customer, Product, SafetyWear, Distributor, ProductCategory, Post, MarketCategory, Config, Contact, Size, MarketSector, NewsArticle
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
import subprocess
import sys
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger('django')


import tarfile

@csrf_exempt
def backup_documents(request):
    """Temporary endpoint to download /data/documents as a tar.gz archive."""
    if not request.user.is_staff:
        return HttpResponse(status=403)
    documents_dir = '/data/documents'
    if not os.path.isdir(documents_dir):
        return HttpResponse('Documents directory not found', status=404)

    import threading

    read_fd, write_fd = os.pipe()

    def write_tar():
        with os.fdopen(write_fd, 'wb') as pipe_out:
            with tarfile.open(fileobj=pipe_out, mode='w:gz') as tar:
                tar.add(documents_dir, arcname='documents')

    thread = threading.Thread(target=write_tar, daemon=True)
    thread.start()

    def stream_pipe():
        with os.fdopen(read_fd, 'rb') as pipe_in:
            while True:
                chunk = pipe_in.read(65536)
                if not chunk:
                    break
                yield chunk
        thread.join()

    response = StreamingHttpResponse(stream_pipe(), content_type='application/x-gzip')
    response['Content-Disposition'] = 'attachment; filename="documents_backup.tar.gz"'
    return response


@csrf_exempt  # Disable CSRF protection just for now (because you're uploading manually)
def upload_file(request):
    #make this a directory if not exists
    if not os.path.exists('/data/documents'):
        os.makedirs('/data/documents')
    if request.method == 'POST' and request.FILES:
        uploaded_files = request.FILES.getlist('files')
        save_path = '/data/documents'  # Railway volume mount
        
        saved_files = []
        for file in uploaded_files:
            file_path = os.path.join(save_path, file.name)
            # if the file already exists, overwrite it
            if os.path.exists(file_path):
                os.remove(file_path)
            # save the file
            # open the file in write-binary mode
            # and write the content of the uploaded file to it
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            threading.Thread(target=downscale_image, args=(file_path,), daemon=True).start()
            saved_files.append(file.name)
            

        return JsonResponse({'status': 'success', 'saved_files': saved_files})
    else:
        return JsonResponse({'error': 'No files uploaded'}, status=400)

def getFileFromBase64(data, filename):
    format, imgstr = data.split(';base64,')
    ext = format.split('/')[-1]
    fname = filename + '.' + ext
    raw = base64.b64decode(imgstr)

    # Attempt downscale in-memory before saving
    try:
        img = Image.open(io.BytesIO(raw))
        orig_fmt = img.format or ext.upper()
        img, changed = _prepare_image(img, orig_fmt)
        if changed:
            buf = io.BytesIO()
            save_kwargs = {'quality': JPEG_QUALITY, 'optimize': True} if orig_fmt == 'JPEG' else {}
            img.save(buf, orig_fmt, **save_kwargs)
            raw = buf.getvalue()
    except Exception:
        pass  # Not an image — leave raw bytes unchanged

    return ContentFile(raw, name=fname)


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

def mail_admin_async(subject, content, reply_to=None):
    """Send email asynchronously using management command"""
    try:
        cmd = [
            sys.executable, 'manage.py', 'send_email',
            '--subject', subject,
            '--body', content,
            '--to', settings.EMAIL_ADMIN,
            '--from-email', settings.EMAIL_FROM
        ]
        
        if reply_to:
            cmd.extend(['--reply-to', reply_to])
        
        # Run command in background without waiting for completion
        subprocess.Popen(cmd, cwd=settings.BASE_DIR)
        
    except Exception as e:
        logger.error(f"Failed to start async email process: {e}")

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
@api_view(['GET'])
def customers_list(request):
    if request.user.profile.profileType == 'admin':
        custs = CustomerSerializer(Customer.objects.all().order_by('businessName'), many=True).data
        return JsonResponse(custs, safe=False)

    customers = request.user.profile.distributor.customers.prefetch_related(
        'products', 'user', 'products__productCategory', 'products__subCategory').order_by('businessName')
    serializer = CustomerSerializer(customers, many=True)
    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@api_view(['GET'])
def sds_products(request):
    products = Product.objects.filter(sdsSheet__isnull=False).exclude(sdsSheet='').values('id', 'name', 'brand')
    return JsonResponse(list(products), safe=False)


@csrf_exempt
@api_view(['GET'])
def info_sheet_products(request):
    products = Product.objects.filter(infoSheet__isnull=False).exclude(infoSheet='').values('id', 'name', 'brand')
    return JsonResponse(list(products), safe=False)


@csrf_exempt
@api_view(['GET'])
def products_list(request):
    print(datetime.datetime.now(), "products_list called by", request.user)

    user = request.user
    profile = getattr(user, "profile", None)
    is_customer = getattr(profile, "profileType", None) == "customer"

    # Base queryset
    if is_customer:
        try:
            products_qs = profile.customer.products.all()
        except Customer.DoesNotExist:
            products_qs = Product.objects.none()
    else:
        products_qs = Product.objects.all()

    # Optimized related loading
    products_qs = products_qs.prefetch_related(
        'productCategory',
        'subCategory',
        'markets',
        'safetyWears',
        'sizes',
        'customers',
    )

    # Serialize once
    serializer = ProductSerializer(products_qs, many=True, context={"user": user})
    data = serializer.data

    print(datetime.datetime.now(), "products_list completed for", request.user)
    print("Products list length:", len(data))
    return JsonResponse(data, safe=False)

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
    customer.products.set(products)
    customer.created_at = datetime.datetime.now()
    customer.profileType = "customer"
    customer.save()
    request.user.profile.distributor.customers.add(customer)

    return JsonResponse({"message": "customer saved"})


@transaction.atomic
@csrf_exempt
def special_customer_edit(request):
    """
    This endpoint is for special cases where a customer needs to be edited without being logged in.
    It is not recommended for regular use and should be used with caution.
    """
    dataas = json.loads(request.body)
    allProducts = []
    for data in dataas: 
        try:
            customer = Customer.objects.get(pk=data.get('id'))
            print(customer)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer does not exist"}, status=404)

        ids = [b for b in data.get('products') if isinstance(b, int)]
        names = [b.strip() for b in data.get('products') if isinstance(b, str)]

        products = Product.objects.filter(Q(pk__in=ids) | Q(name__in=names))
        print(products)
        customer.products.set(products)
        allProducts.extend([p.id for p in products if p not in allProducts])
        customer.updated_at = datetime.datetime.now()
        customer.save()

    return JsonResponse({"message": "customers edited", "products": allProducts})

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

    customer.products.set(products)
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
        # Set the user's profile type to distributor
        user.profile.profileType = 'distributor'
        user.profile.save()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=422)

    try:
        distributor = Distributor.objects.create(
            phoneNumber=data.get('phoneNumber'),
            cellPhoneNumber=data.get('cellPhoneNumber'),
            businessName=data.get('businessName'),
            profileType='distributor',
            geocodingDetail=data.get('geocodingDetail'),
            address=data.get('address'),
            primaryImageLink=createImage(data.get('primaryImageLink')),
        )
        distributor.save()
        # Add the user to the distributor's users
        distributor.users.add(user)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=422)

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

    # Update the first user's details for backward compatibility
    first_user = distributor.users.first()
    if first_user:
        first_user.first_name = data.get('first_name')
        first_user.last_name = data.get('last_name')
        first_user.email = data.get('email')
        first_user.save()

    distributor.address = data.get('address')
    distributor.businessname = data.get('businessName')
    distributor.phonenumber = data.get('phoneNumber')
    distributor.cellphonenumber = data.get('cellPhoneNumber')

    if data.get('geocodingDetail'):
        distributor.geocodingdetail = data.get('geocodingDetail')

    if data.get('primaryImageLink') and not distributor.primaryimagelink == data.get('primaryImageLink'):
        distributor.primaryimagelink = createImage(data.get('primaryImageLink'))

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
            procedure=data.get('procedure'),
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
    product.procedure = data.get('procedure')
    product.description = data.get('description')
    product.subCategory = data.get('subCategory')
    product.markets = MarketCategory.objects.filter(pk__in=data.get('markets'))

    for key in ['productCategory', 'subCategory']:
        if data.get(key):
            setattr(product, key, ProductCategory.objects.filter(pk__in=data.get(key)))

    if data.get('sizes'):
        product.sizes = Size.objects.filter(pk__in=data.get('sizes'))
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
    try:
        # Check if user has a profile
        if not hasattr(request.user, 'profile'):
            return JsonResponse({'error': 'User has no profile'}, status=400)

        data = UserSerializer(request.user).data
        data['emails'] = [u.email for u in User.objects.all()]
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': f'Error fetching user details: {str(e)}'}, status=500)


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
        customers = CustomerSerializer(Customer.objects.all().order_by('businessName'), many=True).data
        return JsonResponse({"customers": customers, "products": products})
    else:
        return JsonResponse({"error": "evildoer"})


@csrf_exempt
@api_view(['GET'])
def customers_table(request):
    profile = request.user.profile
    if profile.profileType == "distributor":
        products = profile.distributor.products.only('id', 'name')
        customers = CustomerSerializer(profile.distributor.customers.order_by('businessName'), many=True).data
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
@cache_control(public=True, max_age=10, stale_while_revalidate=60)
def public_products(request):
    try:
        p = Product.objects.prefetch_related(
            'productCategory', 'subCategory', 'markets', 'safetyWears', 'sizes'
        ).filter(public=True).order_by('name')
        products = PublicProductSerializer(p, many=True).data
        categories = CategorySerializer(ProductCategory.objects.all(), many=True).data
        posts = PostSererializer(Post.objects.all(), many=True).data
        news_posts = NewsPostSerializer(NewsArticle.objects.all(), many=True).data
        markets = MarketSerializer(MarketCategory.objects.all(), many=True).data
        configs = ConfigSerializer(Config.objects.all(), many=True).data
        sizes = SizeSerializer(Size.objects.all(), many=True).data
        sectors = SectorSerializer(MarketSector.objects.all(), many=True).data
        return JsonResponse(
            {'products': products, 'categories': categories, 'posts': posts,
             'markets': markets, 'configs': configs, 'sizes': sizes,
             'sectors': sectors, 'news_posts': news_posts}, safe=False)
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
def sectors_list(request):
    if request.user:
        data = SectorSerializer(MarketSector.objects.all(), many=True).data
        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'evildoer'})

@csrf_exempt
@api_view(['GET'])
def news_post_list(request):
    if request.user:
        #data = NewsPostSerializer(NewsArticle.objects.all(), many=True).data
        #return JsonResponse(data, safe=False)
        pass

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

    #cap_value = b.pop("captcha_token")
    #r = requests.post('https://www.google.com/recaptcha/api/siteverify',
    #                    { 'secret': settings.RECAPTCHA_PRIVATE_KEY, 'response': cap_value })
    #res = r.json()
    #if not res.get('success') or res.get('score', 0) < 0.7:
    #    raise ValidationError('There was a problem with your request, please try again', code="recaptcha")

    c = ContactSerializer(data=b)
    c.is_valid()
    a = c.validated_data
    c.create(a)

    # Push the full submission to OnePageCRM (tag + note with the message).
    # Isolated so a CRM outage never breaks the contact form.
    try:
        push_contact_to_onepagecrm(b)
    except Exception as crm_err:
        logger.error("OnePageCRM contact push failed: %s", crm_err)

    company = b.get('companyName') or ''
    admin_body = 'Name: ' + b['nameFrom'] + '\nEmail: ' + b['emailFrom']
    if company:
        admin_body += '\nCompany: ' + company
    admin_body += '\n\nMessage:\n' + b['content']
    mail_admin_async('Contact from Geller.co.nz',
        admin_body,
        reply_to=b['emailFrom']
    )
    mail_customer('Contact from Geller.co.nz',
        'Hi ' + b['nameFrom'] + ',\n\nThanks for you contact request we will be in touch shortly.',
        b['emailFrom']
    )

    # Return response even if there is an error. 
    return JsonResponse({'sddsfds':'sdfsefsfseffse'})

def _onepagecrm_create_contact_with_note(name, email, note_text, tags, company_name=''):
    """Create (or let OnePageCRM dedupe) a contact and attach a note. Returns the
    contact id. Auth is HTTP Basic (user_id : api_key). Raises RuntimeError with the
    HTTP body on any non-OK response so callers can log a useful reason.
    """
    base = settings.ONEPAGECRM_ENDPOINT.rstrip('/')
    auth = (settings.ONEPAGECRM_USER_ID, settings.ONEPAGECRM_API_KEY)

    # Split the single "name" field into first/last for OnePageCRM.
    full_name = (name or '').strip()
    first_name, _, last_name = full_name.partition(' ')
    if not first_name:
        first_name = full_name or 'Unknown'

    contact_payload = {
        'first_name': first_name,
        'last_name': last_name,
        'company_name': company_name or '',
        'emails': [{'type': 'work', 'value': email or ''}],
        'tags': tags,
    }
    create_resp = requests.post(
        base + '/contacts.json', json=contact_payload, auth=auth, timeout=10,
    )
    if not create_resp.ok:
        raise RuntimeError('create contact failed: HTTP {} {}'.format(
            create_resp.status_code, create_resp.text[:500]))
    contact_id = create_resp.json()['data']['contact']['id']

    if note_text:
        note_resp = requests.post(
            base + '/contacts/{}/notes.json'.format(contact_id),
            json={'contact_id': contact_id, 'text': note_text}, auth=auth, timeout=10,
        )
        if not note_resp.ok:
            raise RuntimeError('add note failed: HTTP {} {}'.format(
                note_resp.status_code, note_resp.text[:500]))
    return contact_id


def push_sds_to_onepagecrm(b):
    """Push an SDS-download lead into OnePageCRM as a contact tagged with the product,
    plus a note recording the download. `b` must contain nameFrom, emailFrom,
    productName, productId, and optionally companyName.

    Best-effort: the caller swallows+logs any failure so it never blocks the download.
    """
    product_name = b.get('productName', '')
    contact_id = _onepagecrm_create_contact_with_note(
        name=b.get('nameFrom'),
        email=b.get('emailFrom'),
        note_text='Downloaded SDS for product: {} (id {})'.format(product_name, b.get('productId')),
        tags=['Download SDS for {}'.format(product_name)],
        company_name=b.get('companyName'),
    )
    logger.info("OnePageCRM SDS push OK: contact %s, product '%s'", contact_id, product_name)
    return contact_id


def push_contact_to_onepagecrm(b):
    """Push a Contact-Us form submission into OnePageCRM: a contact tagged
    'Geller Website Enquiry' plus a note containing the full message the user typed.
    `b` must contain nameFrom, emailFrom, content, and optionally companyName.

    Best-effort: the caller swallows+logs any failure so it never blocks the form.
    """
    message = b.get('content') or ''
    note_text = 'Contact form submission from geller.co.nz\n\nName: {}\nEmail: {}\n\nMessage:\n{}'.format(
        b.get('nameFrom', ''), b.get('emailFrom', ''), message)
    contact_id = _onepagecrm_create_contact_with_note(
        name=b.get('nameFrom'),
        email=b.get('emailFrom'),
        note_text=note_text,
        tags=['Geller Website Enquiry'],
        company_name=b.get('companyName'),
    )
    logger.info("OnePageCRM contact push OK: contact %s, email %s", contact_id, b.get('emailFrom'))
    return contact_id


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

        # Push the lead to OnePageCRM (tag + note). Isolated so a CRM outage
        # never breaks the SDS download for the customer.
        try:
            push_sds_to_onepagecrm(b)
        except Exception as crm_err:
            logger.error("OnePageCRM SDS push failed: %s", crm_err)

        mail_admin_async(
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
        raise Http404("Document could not be found.")
    except Http404:
        raise
    except Exception as e:
        # Dump the error into alllogs.log
        logger.error(e)
        raise Http404("Document was not found.")
