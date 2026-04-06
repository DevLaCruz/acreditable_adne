from django.shortcuts import render
from store.models import Product, ReviewRating
from category.models import Category


def home(request):
    # Obtener solo los 8 productos más recientes
    products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    categories = Category.objects.exclude(cat_image='').order_by('-id')[:3]

    reviews = {}  # Diccionario para almacenar reseñas por producto
    for product in products:
        reviews[product.id] = ReviewRating.objects.filter(product_id=product.id, status=True)

    context = {
        'products': products,  # Solo 8 productos más recientes
        'reviews': reviews,
        'categories': categories,  # Agregar categorías al contexto
    }

    return render(request, 'home.html', context)
