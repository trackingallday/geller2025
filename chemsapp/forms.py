from django import forms
from django.forms import ModelForm
from django.forms.widgets import TextInput
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Post, ProductCategory, Distributor, Profile, Product, PricingVariant

class PricingVariantForm(ModelForm):
    class Meta:
        model = PricingVariant
        fields = '__all__'

    def clean(self):
        """Stop a customer having two prices for the same product.

        The check lives here and not on the model, because Django writes the
        many-to-many rows after it saves the object. self.customers is empty
        during Model.clean() on a new object.
        """
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        customers = cleaned_data.get('customers')
        if not product or not customers:
            return cleaned_data

        clashes = PricingVariant.objects.filter(
            product=product, customers__in=customers).exclude(pk=self.instance.pk)
        if clashes.exists():
            clashing_names = ', '.join(
                str(customer) for customer in customers.filter(pricing_variants__in=clashes).distinct())
            raise ValidationError(
                'These customers already have a price for {}: {}'.format(product.name, clashing_names))
        return cleaned_data


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'wall_chart_color': TextInput(attrs={'type': 'color'}),
        }


class ProductCategoryForm(ModelForm):
    class Meta:
        model = ProductCategory
        fields = '__all__'
        widgets = {
            'menu_color': TextInput(attrs={'type': 'color'}),
        }

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'linkColor': TextInput(attrs={'type': 'color'}),
        }

class SpecialPostForm(ModelForm):
    """Form for editing special posts with readonly name field"""
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'linkColor': TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super(SpecialPostForm, self).__init__(*args, **kwargs)
        # Make the name field readonly
        if self.instance and self.instance.pk:
            self.fields['name'].disabled = True
            self.fields['name'].widget.attrs['readonly'] = True


class DistributorUserInlineForm(forms.ModelForm):
    """Form for creating/editing users within the Distributor admin"""
    username = forms.CharField(
        max_length=150,
        required=False,
        help_text="Required for new users. Leave blank to only link existing user."
    )
    email = forms.EmailField(
        required=False,
        help_text="Email address for the user"
    )
    first_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="User's first name"
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="User's last name"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        required=False,
        help_text="Leave blank to generate random password or for user to set via password reset"
    )
    phone_number = forms.CharField(
        max_length=100,
        required=False,
        help_text="Phone number (stored in Profile)"
    )
    auto_generate_password = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Check to auto-generate a secure password"
    )
    send_password_reset = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Send password reset email to user"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing existing user, populate the phone number from profile
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.profile
                self.fields['phone_number'].initial = profile.phoneNumber
            except Profile.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        auto_generate = cleaned_data.get('auto_generate_password')

        # If username is provided, we're creating a new user
        if username and not self.instance.pk:
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                raise ValidationError({'username': 'A user with this username already exists.'})

            # Validate password if provided and not auto-generating
            if password and not auto_generate:
                try:
                    validate_password(password)
                except ValidationError as e:
                    raise ValidationError({'password': e.messages})

        return cleaned_data

    def save(self, commit=True):
        user = self.instance

        # Check if we're creating a new user
        if not user.pk and self.cleaned_data.get('username'):
            # Create new user
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data.get('email', ''),
                first_name=self.cleaned_data.get('first_name', ''),
                last_name=self.cleaned_data.get('last_name', '')
            )

            # Set password
            if self.cleaned_data.get('auto_generate_password'):
                # Generate random password
                password = User.objects.make_random_password(length=12)
                user.set_password(password)
                user.save()
            elif self.cleaned_data.get('password'):
                user.set_password(self.cleaned_data['password'])
                user.save()
            else:
                # No password set - user will need to use password reset
                user.set_unusable_password()
                user.save()

            # Create or update profile
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'phoneNumber': self.cleaned_data.get('phone_number', ''),
                    'businessName': user.get_full_name() or user.username,
                    'address': '',
                    'profileType': 'distributor'
                }
            )
            if not created:
                profile.phoneNumber = self.cleaned_data.get('phone_number', '')
                profile.save()

            self.instance = user
        elif user.pk:
            # Update existing user
            user.email = self.cleaned_data.get('email', user.email)
            user.first_name = self.cleaned_data.get('first_name', user.first_name)
            user.last_name = self.cleaned_data.get('last_name', user.last_name)

            # Update password if provided
            if self.cleaned_data.get('password'):
                user.set_password(self.cleaned_data['password'])
            elif self.cleaned_data.get('auto_generate_password'):
                password = User.objects.make_random_password(length=12)
                user.set_password(password)

            if commit:
                user.save()

            # Update profile phone number
            try:
                profile = user.profile
                profile.phoneNumber = self.cleaned_data.get('phone_number', profile.phoneNumber)
                profile.save()
            except Profile.DoesNotExist:
                Profile.objects.create(
                    user=user,
                    phoneNumber=self.cleaned_data.get('phone_number', ''),
                    businessName=user.get_full_name() or user.username,
                    address='',
                    profileType='distributor'
                )

        return user


class DistributorAdminForm(forms.ModelForm):
    """Custom form for Distributor admin with enhanced validation"""

    class Meta:
        model = Distributor
        fields = '__all__'
        help_texts = {
            'businessname': 'The name of the distributor business',
            'phonenumber': 'Primary contact phone number',
            'cellphonenumber': 'Mobile/cell phone number',
            'address': 'Physical address of the distributor',
            'users': 'Select existing users or create new users using the "Create new user for distributor" action',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make users field optional and add helpful text
        self.fields['users'].help_text = 'Select existing users to associate with this distributor. Use the "Quick Actions" link above to create new users.'
        self.fields['users'].required = False