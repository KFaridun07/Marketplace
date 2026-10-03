from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    fullname = models.CharField(max_length = 100)
    avatar = models.ImageField(upload_to='profiles/', blank=True,null= True)
    user = models.OneToOneField(User,on_delete=models.CASCADE)



class Category(models.Model):
    title  = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class Product(models.Model):
    name = models.CharField( max_length=50)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE,related_name='products_category')
    price = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()


class Order(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.IntegerField()
    cr_at = models.DateField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.IntegerField()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='images')
    image = models.ImageField(upload_to='iamges/',blank=True,null=True)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)






