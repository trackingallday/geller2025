from django.forms import ModelForm
from django.forms.widgets import TextInput
from .models import Post, ProductCategory

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