from django.shortcuts import render,redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView,DetailView,ListView,View,UpdateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView,LogoutView
from .models import *
from .forms import *
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.contrib.auth.models import User
from .utils import ask_ai
# Create your views here.

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'register.html'
    success_url = reverse_lazy('login')

class Login(LoginView):
    template_name = 'login.html'
    next_page = 'cr_profile'

class Logout(LogoutView):
    next_page = 'login'

class CreateProfile(LoginRequiredMixin,CreateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'create.profile.html'

    def dispatch(self, request, *args, **kwargs):
        if Profile.objects.filter(user = self.request.user).exists():
            profile = Profile.objects.get(user = self.request.user)
            return redirect('myprofile',pk = profile.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('myprofile',kwargs = {'pk':self.object.pk})

class ProfileDetail(LoginRequiredMixin,DetailView):
    model = Profile
    template_name = 'my_profile.html'
    context_object_name = 'profile'

    def get_queryset(self):
        return Profile.objects.filter(user = self.request.user)

class ProfileEdit(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'edit_profile.html'

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('myprofile', kwargs={'pk': self.object.pk})


class CategoryCreate(LoginRequiredMixin,CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'create_cat.html'
    success_url = reverse_lazy('cats')


class CategoryList(ListView):
    model = Category
    template_name = 'categorys.html'
    context_object_name = 'cats'

class ProductCreate(LoginRequiredMixin,CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'create_product.html'
    success_url = reverse_lazy('products')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    


class ProductList(ListView):
    model = Product
    template_name = 'products.html'
    context_object_name = 'products'

class ProductDetail(DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(user=self.request.user,product=self.object).exists()
        else:
            context['is_favorite'] = False

        return context

class ProductEdit(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'edit_product.html'

    def get_queryset(self):
        return Product.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy('product', kwargs={'pk': self.object.pk})




class ImageCreate(LoginRequiredMixin,CreateView):
    model = ProductImage
    form_class = ImageForm
    template_name = 'add_image.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        product = form.cleaned_data['product']

        if product.owner == self.request.user:
            self.object = form.save()

            return redirect('images_pr', pk=product.pk)

        messages.error(self.request,'Вы не можете добавить фото к чужому товару.')

        return redirect('cr_image')



class ImageList(ListView):
    model = ProductImage
    template_name = 'images_product.html'
    context_object_name = 'images'

    def get_queryset(self):
        return ProductImage.objects.filter(product_id=self.kwargs['pk'])


class AddToCart(LoginRequiredMixin,View):
    def post(self, request, pk):

        try:
            product = Product.objects.get(pk=pk)

        except Product.DoesNotExist:
            messages.error(request, 'Товар не найден.')
            return redirect('products')

        if product.owner == request.user:
            messages.error(request,'Вы не можете добавить свой товар в корзину.')
            return redirect('product', pk=product.pk)

        if Cart.objects.filter(owner=request.user).exists():
            cart = Cart.objects.get(owner=request.user)
        else:
            cart = Cart.objects.create(owner=request.user)

        if CartItem.objects.filter(cart=cart,product=product).exists():

            item = CartItem.objects.get(cart=cart,product=product)

            item.quantity += 1
            item.save()

        else:
            CartItem.objects.create(cart=cart,product=product,quantity=1)

        return redirect('product', pk=product.pk)



class CartList(LoginRequiredMixin,View):
    def get(self, request):

        if Cart.objects.filter(owner=request.user).exists():
            cart = Cart.objects.get(owner=request.user)
            items = CartItem.objects.filter(cart=cart)
        else:
            cart = None
            items = []

        total_price = 0

        for item in items:
            total_price += item.product.price * item.quantity

        return render(request, 'cart.html', {'cart': cart,'items': items,'total_price': total_price})





class OrderView(LoginRequiredMixin,View):

    def post(self, request):

        if Cart.objects.filter(owner=request.user).exists():
            cart = Cart.objects.get(owner=request.user)
        else:
            messages.error(request, 'Корзина пуста.')
            return redirect('cart')

        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            messages.error(request, 'Корзина пуста.')
            return redirect('cart')

        total_price = 0

        for item in cart_items:

            if item.product.owner == request.user:
                messages.error(request,f'Вы не можете заказать свой товар: {item.product.name}')
                return redirect('cart')

            total_price += item.product.price * item.quantity

        order = Order.objects.create(owner=request.user,total_price=total_price)

        for item in cart_items:

            OrderItem.objects.create(order=order,product=item.product,quantity=item.quantity,price=item.product.price)

        cart_items.delete()

        return redirect('order_detail', pk=order.pk)

class OrderList(LoginRequiredMixin,ListView):
    model = Order
    template_name = 'orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(owner=self.request.user)



class OrderDetail(LoginRequiredMixin,DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(owner=self.request.user)



class DeleteCartItem(LoginRequiredMixin,View):
    def post(self, request, pk):
        item = CartItem.objects.get(pk=pk)

        if item.cart.owner == request.user:
            item.delete()

        return redirect('cart')

class ChangeCartQuantity(LoginRequiredMixin,View):
    def post(self, request, pk):
        item = CartItem.objects.get(pk=pk)

        if item.cart.owner == request.user:

            action = request.POST.get('action')

            if action == 'plus':
                item.quantity += 1
                item.save()

            elif action == 'minus':
                if item.quantity > 1:
                    item.quantity -= 1
                    item.save()
                else:
                    item.delete()

        return redirect('cart')


class DeleteProduct(LoginRequiredMixin,View):
    def post(self, request, pk):

        try:
            product = Product.objects.get(pk=pk)

        except Product.DoesNotExist:
            messages.error(request, 'Товар не найден.')
            return redirect('products')

        if product.owner == request.user:
            product.delete()
            return redirect('products')

        else:
            return redirect('product', pk=product.pk)


class CategoryProducts(View):
    def get(self, request, pk):

        try:
            category = Category.objects.get(pk=pk)

        except Category.DoesNotExist:
            messages.error(request, 'Категория не найдена.')
            return redirect('cats')

        products = Product.objects.filter(category=category)

        return render(request, 'category_products.html', {'category': category,'products': products})


class Home(View):
    def get(self, request):
        categories = Category.objects.all()

        search = request.GET.get('search')
        category_id = request.GET.get('category')

        if search and category_id:
            products = Product.objects.filter(name__icontains=search,category_id=category_id)

        elif search:
            products = Product.objects.filter(name__icontains=search)

        elif category_id:
            products = Product.objects.filter(category_id=category_id)

        else:
            products = Product.objects.all()

        return render(request, 'home.html', {'categories': categories,'products': products})


class AddFavorite(LoginRequiredMixin,View):
    def post(self, request, pk):
        product = Product.objects.get(pk=pk)

        if product.owner == request.user:
            return redirect('product', pk=product.pk)

        if Favorite.objects.filter(user=request.user,product=product).exists():
            return redirect('product', pk=product.pk)

        Favorite.objects.create(user=request.user,product=product)

        return redirect('product', pk=product.pk)

class MyProducts(LoginRequiredMixin,ListView):
    model = Product
    template_name = 'my_products.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(owner=self.request.user)

class MyFavorites(LoginRequiredMixin,View):
    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user)

        products = []

        for favorite in favorites:
            products.append(favorite.product)

        return render(request, 'my_favorites.html', {'products': products})

class RemoveFavorite(LoginRequiredMixin,View):
    def post(self, request, pk):

        if Favorite.objects.filter(user=request.user,product_id=pk).exists():

            favorite = Favorite.objects.get(user=request.user,product_id=pk)
            favorite.delete()

        return redirect('my_favorites')


class AdminDashboard(View):

    def get(self, request):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        return render(request, 'admin_dashboard.html')

class AdminUsers(View):

    def get(self, request):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        users = User.objects.all()

        return render(request, 'admin_users.html', {'users': users})

class AdminUserDetail(View):

    def get(self, request, pk):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        user = User.objects.get(pk=pk)

        return render(request, 'admin_user_detail.html', {'user': user})


class AdminCategories(View):

    def get(self, request):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        categories = Category.objects.all()

        return render(request,'admin_categories.html',{'categories': categories})

class AdminProducts(View):

    def get(self, request):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        products = Product.objects.all()

        return render(request,'admin_products.html',{'products': products})


class AdminOrders(View):

    def get(self, request):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        orders = Order.objects.all()

        return render(request,'admin_orders.html',{'orders': orders})


class AdminOrderDetail(View):

    def get(self, request, pk):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        order = Order.objects.get(pk=pk)

        order_items = OrderItem.objects.filter(order=order)

        return render(request,'admin_order_detail.html',{'order': order,'order_items': order_items})


class AdminCategoryCreate(View):

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        form = CategoryForm()

        return render(request, 'admin_category_create.html', {'form': form})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('admin_categories')

        return render(request, 'admin_category_create.html', {'form': form})


class AdminCategoryEdit(View):

    def get(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        category = Category.objects.get(pk=pk)

        form = CategoryForm(instance=category)

        return render(request,'admin_category_edit.html',{'form': form})

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        category = Category.objects.get(pk=pk)

        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()
            return redirect('admin_categories')

        return render(request,'admin_category_edit.html',{'form': form})

class AdminCategoryDelete(View):

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        category = Category.objects.get(pk=pk)

        category.delete()

        return redirect('admin_categories')

class AdminUserDelete(View):

    def post(self, request, pk):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        user = User.objects.get(pk=pk)

        if user == request.user:
            return HttpResponse('You cannot delete yourself')

        user.delete()

        return redirect('admin_users')

class AdminProductDelete(View):

    def post(self, request, pk):

        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.is_superuser:
            return HttpResponse('Access denied')

        product = Product.objects.get(pk=pk)

        product.delete()

        return redirect('admin_products')


class AIView(LoginRequiredMixin, View):

    def get(self, request):
        return render(request, 'ai.html')

    def post(self, request):
        question = request.POST.get('question')

        products = Product.objects.all()

        answer = ask_ai(question, products)

        return render(request, 'ai.html', {
            'answer': answer
        })








    



    
