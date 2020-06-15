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