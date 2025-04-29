from django.shortcuts import render
from store.models import Product, ReviewRating
from category.models import Category
from PIL import Image
import os

def home(request):
    # Obtener solo los 8 productos más recientes
    products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    categories = Category.objects.all()  # Obtener todas las categorías  
    
    reviews = {}  # Diccionario para almacenar reseñas por producto
    for product in products:
        reviews[product.id] = ReviewRating.objects.filter(product_id=product.id, status=True)

    context = {
        'products': products,  # Solo 8 productos más recientes
        'reviews': reviews,
        'categories': categories,  # 🔹 Agregar categorías al contexto
    }

    return render(request, 'home.html', context)

def convert_to_webp(instance, field_name):
    """Convierte la imagen a WebP y elimina la original."""
    imagen_field = getattr(instance, field_name)
    if imagen_field and imagen_field.path:
        ruta_original = imagen_field.path
        ruta_webp = os.path.splitext(ruta_original)[0] + ".webp"

        # Convertir la imagen a WebP
        with Image.open(ruta_original) as img:
            img.save(ruta_webp, 'WEBP', quality=80)

        # Reemplazar la imagen en la BD
        imagen_field.name = os.path.splitext(imagen_field.name)[0] + ".webp"
        instance.save(update_fields=[field_name])

        # Eliminar la imagen original
        if os.path.exists(ruta_original):
            os.remove(ruta_original)