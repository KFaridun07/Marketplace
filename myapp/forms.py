from django import forms 
from .models import *


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['fullname','avatar']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['title']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','description','price','category']

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError('price must be positive')
        return price

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity < 0:
            raise forms.ValidationError('quantity must be positive')
        return quantity

class ImageForm(forms.ModelForm):

    class Meta:
        model = ProductImage
        fields = ['product', 'image']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')

        super().__init__(*args, **kwargs)

        self.fields['product'].queryset = Product.objects.filter(owner=user)
        
        