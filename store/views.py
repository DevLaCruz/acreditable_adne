from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct


def store(request, category_slug=None):
    """
    Muestra la lista de productos en la tienda, filtrados opcionalmente por categoría.
    """
    categories = None
    products = None

    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(
            category=categories, is_available=True).order_by('id')
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')

    paginator = Paginator(products, 5)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    """
    Muestra los detalles de un producto, incluidas las variaciones asociadas.
    """
    try:
        single_product = Product.objects.get(
            category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(
            request), product=single_product).exists()
    except Product.DoesNotExist:
        raise Http404("Product not found")

    # Verificar si el usuario ha comprado el producto
    orderproduct = None
    if request.user.is_authenticated:
        orderproduct = OrderProduct.objects.filter(
            user=request.user, product=single_product).exists()

    # Obtener las reseñas y galería de imágenes
    reviews = ReviewRating.objects.filter(product=single_product, status=True)
    product_gallery = ProductGallery.objects.filter(product=single_product)

    # Obtener las variaciones categorizadas del producto
    variation_dict = {}
    for variation in single_product.variations.filter(is_active=True):
        category_name = variation.variation_category.name
        if category_name not in variation_dict:
            variation_dict[category_name] = []
        variation_dict[category_name].append(variation.variation_value)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'variation_dict': variation_dict,
    }

    return render(request, 'store/product_detail.html', context)


def search(request):
    """
    Permite buscar productos por palabras clave en nombre o descripción.
    """
    products = []
    product_count = 0

    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()

    context = {
        'products': products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    """
    Permite a los usuarios enviar o actualizar reseñas para un producto específico.
    """
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            # Actualizar una reseña existente
            review = ReviewRating.objects.get(
                user=request.user, product_id=product_id)
            form = ReviewForm(request.POST, instance=review)
            if form.is_valid():
                form.save()
                messages.success(
                    request, 'Muchas gracias, tu comentario ha sido actualizado.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            # Crear una nueva reseña
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user = request.user
                data.save()
                messages.success(
                    request, 'Muchas gracias, tu comentario fue enviado con éxito.')
            return redirect(url)
