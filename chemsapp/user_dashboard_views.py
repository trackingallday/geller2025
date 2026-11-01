"""Staff user management: the one admin area that had no interface at all.

``UserAdmin`` and ``ProfileAdmin`` are registered with empty bodies, so until
now creating a staff user meant the Django user form plus a separate profile,
or the one-off ``create-user`` view hanging off a distributor. These endpoints
put the whole job in one place for the admin app.
"""
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string

from .models import Customer, Distributor, Profile
from .staff_api import error, form_data, json_body, ok, staff_api

# A page of users at a time. The list is a search tool, not a report.
PAGE_SIZE = 50


def _profile_of(user):
    """The user's profile, or None.

    ``Customer`` inherits ``Profile`` by multi-table inheritance, so a
    customer's row is reachable either way; this returns the base row.
    """
    return Profile.objects.filter(user=user).first()


def _serialize(user, profile=None):
    """One user as the admin app's list and detail both want them."""
    profile = profile if profile is not None else _profile_of(user)
    distributors = [
        {'id': d.pk, 'name': d.businessname}
        for d in user.distributors.all()
    ]

    return {
        'id': user.pk,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'date_joined': user.date_joined.isoformat() if user.date_joined else None,
        'profile': {
            'profile_type': profile.profileType,
            'business_name': profile.businessName,
            'phone_number': profile.phoneNumber,
            'cell_phone_number': profile.cellPhoneNumber,
            'has_set_password': profile.hasSetPassword,
        } if profile else None,
        'distributors': distributors,
    }


@staff_api
def user_list(request):
    """Search and page the user list.

    ``q`` matches username, name or email. ``role`` filters on the profile
    type, with the two Django flags offered as roles of their own because
    "who are the staff" is the question this screen is opened to answer.
    """
    search = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()

    users = User.objects.all().prefetch_related('distributors')

    if search:
        users = users.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )

    if role == 'staff':
        users = users.filter(is_staff=True)
    elif role == 'superuser':
        users = users.filter(is_superuser=True)
    elif role:
        users = users.filter(profile__profileType=role)

    total = users.count()

    try:
        page = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page = 1
    start = (page - 1) * PAGE_SIZE
    rows = users.order_by('username')[start:start + PAGE_SIZE]

    # One query for the profiles of this page, rather than one per row.
    profiles = {
        p.user_id: p
        for p in Profile.objects.filter(user__in=[u.pk for u in rows])
    }

    return ok({
        'users': [_serialize(u, profiles.get(u.pk)) for u in rows],
        'total': total,
        'page': page,
        'page_size': PAGE_SIZE,
        'has_more': start + PAGE_SIZE < total,
    })


@staff_api
def user_detail(request, user_id):
    """One user, with the profile and distributor links the list omits."""
    user = get_object_or_404(
        User.objects.prefetch_related('distributors'), pk=user_id)
    data = _serialize(user)
    data['customers'] = list(
        Customer.objects.filter(
            distributors__users=user).values_list('businessName', flat=True)
    ) if user.distributors.exists() else []
    return ok(data)


@staff_api
def create_user(request):
    """Create a user, and optionally link it to a distributor.

    No password is set here. The user is sent a reset email instead, so a
    password never passes through this endpoint or the admin app. A token is
    minted automatically by the post_save signal on User.
    """
    if request.method != 'POST':
        return error('Use POST to create a user.', status=405)

    data = form_data(request)
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()

    if not username:
        return error('A username is required.', status=400)
    if User.objects.filter(username__iexact=username).exists():
        return error(f'The username "{username}" is taken.', status=409)
    if email and User.objects.filter(email__iexact=email).exists():
        return error(f'A user with the email "{email}" already exists.',
                     status=409)

    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=(data.get('first_name') or '').strip(),
        last_name=(data.get('last_name') or '').strip(),
    )
    user.is_staff = bool(data.get('is_staff'))
    user.is_superuser = bool(data.get('is_superuser'))
    # A long random password nobody is told, rather than
    # set_unusable_password(): Django's PasswordResetForm skips any account
    # without a usable password, so marking it unusable here would silently
    # stop the invitation email this endpoint just promised to send.
    user.set_password(get_random_string(50))
    user.save()

    # A post_save signal on User already made a basic Profile, so this fills
    # that row in rather than creating a second one the unique constraint
    # would reject.
    profile = _profile_of(user)
    if profile is not None:
        profile_type = (data.get('profile_type') or '').strip()
        if profile_type:
            profile.profileType = profile_type
        business_name = (data.get('business_name') or '').strip()
        if business_name:
            profile.businessName = business_name
        profile.address = (data.get('address') or '').strip()
        profile.phoneNumber = (data.get('phone_number') or '').strip()
        profile.cellPhoneNumber = (
            data.get('cell_phone_number') or '').strip() or None
        profile.save()

    distributor_id = data.get('distributor_id')
    if distributor_id:
        distributor = Distributor.objects.filter(pk=distributor_id).first()
        if distributor is None:
            return error(f'No distributor with id {distributor_id}.', status=400)
        distributor.users.add(user)

    sent = False
    if email and data.get('send_reset_email', True):
        sent = _send_reset(request, email)

    return ok({**_serialize(user), 'reset_email_sent': sent})


@staff_api
def update_user(request, user_id):
    """Edit a user's details and flags.

    Only the fields present in the request are touched, so the admin app can
    send one changed flag without restating the whole record.
    """
    if request.method not in ('POST', 'PATCH', 'PUT'):
        return error('Use POST or PATCH to edit a user.', status=405)

    user = get_object_or_404(User, pk=user_id)
    data = form_data(request)

    if 'username' in data:
        username = (data.get('username') or '').strip()
        if not username:
            return error('A username is required.', status=400)
        if User.objects.filter(
                username__iexact=username).exclude(pk=user.pk).exists():
            return error(f'The username "{username}" is taken.', status=409)
        user.username = username

    for field, key in (('email', 'email'), ('first_name', 'first_name'),
                       ('last_name', 'last_name')):
        if key in data:
            setattr(user, field, (data.get(key) or '').strip())

    for flag in ('is_active', 'is_staff', 'is_superuser'):
        if flag in data:
            setattr(user, flag, bool(data.get(flag)))

    # A staff user who cannot sign in is a support call waiting to happen,
    # so refuse the combination that causes it rather than saving it.
    if user.is_superuser and not user.is_staff:
        return error('A superuser must also be staff.', status=400)

    user.save()

    profile = _profile_of(user)
    if profile is not None:
        changed = False
        for attr, key in (('profileType', 'profile_type'),
                          ('businessName', 'business_name'),
                          ('address', 'address'),
                          ('phoneNumber', 'phone_number'),
                          ('cellPhoneNumber', 'cell_phone_number')):
            if key in data:
                setattr(profile, attr, (data.get(key) or '').strip())
                changed = True
        if changed:
            profile.save()

    return ok(_serialize(user))


@staff_api
def send_password_reset(request, user_id):
    """Email this user a password reset link."""
    if request.method != 'POST':
        return error('Use POST to send a reset email.', status=405)

    user = get_object_or_404(User, pk=user_id)
    if not user.email:
        return error('This user has no email address to send to.', status=400)

    if not _send_reset(request, user.email):
        return error('That email address was refused by the reset form.',
                     status=400)
    return ok({'id': user.pk, 'email': user.email, 'reset_email_sent': True})


def _send_reset(request, email):
    """Send Django's own reset email. True when it went.

    Uses ``PasswordResetForm`` rather than building the token by hand, the
    same way the distributor admin action does.
    """
    form = PasswordResetForm({'email': email})
    if not form.is_valid():
        return False
    form.save(
        request=request,
        use_https=request.is_secure(),
        email_template_name='registration/password_reset_email.html',
    )
    return True


@staff_api
def distributor_list(request):
    """Distributors, for the picker on the create-user form."""
    search = request.GET.get('q', '').strip()
    rows = Distributor.objects.all()
    if search:
        rows = rows.filter(businessname__icontains=search)
    return ok({'results': [
        {'id': d.pk, 'name': d.businessname}
        for d in rows.order_by('businessname')[:50]
    ]})



def _distributor_data(distributor):
    """A distributor with its people (who sign in for it) and the
    customers it serves."""
    return {
        'id': distributor.pk,
        'name': distributor.businessname,
        'users': [
            {'id': u.pk, 'username': u.username, 'name': u.get_full_name(),
             'email': u.email, 'is_active': u.is_active}
            for u in distributor.users.order_by('username')
        ],
        'customers': [
            {'id': c.pk, 'name': c.businessName}
            for c in distributor.customers.order_by('businessName')
        ],
    }


@staff_api
def distributor_detail(request, distributor_id):
    return ok(_distributor_data(get_object_or_404(Distributor, pk=distributor_id)))


def _set_link(request, distributor_id, relation, model):
    """Link one record to the distributor, or unlink it.

    Body: {id} to link, {id, remove: true} to unlink. Answers with the whole
    distributor, so the screen redraws from one source.
    """
    if request.method != 'POST':
        return error('POST required.', status=405)
    distributor = get_object_or_404(Distributor, pk=distributor_id)
    data = json_body(request)
    try:
        target = model.objects.get(pk=int(data.get('id')))
    except (TypeError, ValueError, model.DoesNotExist):
        return error('That record does not exist.', status=404)
    links = getattr(distributor, relation)
    if data.get('remove'):
        links.remove(target)
    else:
        links.add(target)
    return ok(_distributor_data(distributor))


@staff_api
def distributor_user_link(request, distributor_id):
    return _set_link(request, distributor_id, 'users', User)


@staff_api
def distributor_customer_link(request, distributor_id):
    return _set_link(request, distributor_id, 'customers', Customer)


@staff_api
def distributor_send_resets(request, distributor_id):
    """Email a password reset to every person at the distributor who has an
    email address, as the admin's bulk action did. Says who was skipped."""
    if request.method != 'POST':
        return error('POST required.', status=405)
    distributor = get_object_or_404(Distributor, pk=distributor_id)
    sent, skipped = [], []
    for user in distributor.users.order_by('username'):
        if user.email and _send_reset(request, user.email):
            sent.append(user.username)
        else:
            skipped.append(user.username)
    return ok({'sent': sent, 'skipped': skipped})
