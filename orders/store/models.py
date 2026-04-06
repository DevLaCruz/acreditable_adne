from django.db import models
from category.models import Category
from django.urls import reverse
from accounts.models import Account
from django.db.models import Avg, Count
from core.models import CoreModel
from ckeditor.fields import RichTextField
from PIL import Image
import os

def convert_to_webp(instance, field_name):
    """Converts the image to WebP and deletes the original, skips if already WebP."""
    imagen_field = getattr(instance, field_name)

    if imagen_field and imagen_field.path:
        # Check if the file is already webp
        if imagen_field.name.lower().endswith('.webp'):
            return  # Exit if image is already a WebP

        ruta_original = imagen_field.path
        ruta_webp = os.path.splitext(ruta_original)[0] + ".webp"

        # Convert the image to WebP
        with Image.open(ruta_original) as img:
            img.save(ruta_webp, 'WEBP', quality=80)

        # Update the image field in the database
        imagen_field.name = os.path.splitext(imagen_field.name)[0] + ".webp"
        instance.save(update_fields=[field_name])

        # Delete the original image
        if os.path.exists(ruta_original):
            os.remove(ruta_original)

def product_image_path(instance, filename):
    # store/category_name/product_name/filename
    return f'store/{instance.category.slug}/{instance.slug}/{filename}'

def gallery_image_path(instance, filename):
    # store/category_name/product_name/gallery/filename
    return f'store/{instance.product.category.slug}/{instance.product.slug}/gallery/{filename}'

class Product(CoreModel):
    """
    Representa un producto en la tienda.
    """
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.CharField(max_length=200, unique=True)
    description = RichTextField(blank=True)
    # price = models.IntegerField()
    images = models.ImageField(upload_to=product_image_path)
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    modified_date = models.DateTimeField(auto_now=True)
    # Relación de muchos a muchos con Variation
    variations = models.ManyToManyField('Variation', related_name="products", blank=True)

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name

    def averageReview(self):
        reviews = ReviewRating.objects.filter(
            product=self, status=True).aggregate(average=Avg('rating'))
        avg = reviews['average'] if reviews['average'] is not None else 0
        return float(avg)

    def countReview(self):
        reviews = ReviewRating.objects.filter(
            product=self, status=True).aggregate(count=Count('id'))
        count = reviews['count'] if reviews['count'] is not None else 0
        return int(count)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Guarda la imagen original
        convert_to_webp(self, 'images')  # Convierte a WebP

class VariationCategory(CoreModel):
    """
    Representa un tipo de variación como 'Color', 'Talla', 'Material', etc.
    Puede ser reutilizado entre múltiples productos.
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Variation(CoreModel):
    """
    Representa un valor específico dentro de una categoría de variación.
    Ejemplo: Color - Rojo, Talla - M.
    Puede ser compartido entre múltiples productos.
    """
    variation_category = models.ForeignKey(
        VariationCategory, on_delete=models.CASCADE, related_name="variations")
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.variation_category.name}: {self.variation_value}"


class ReviewRating(CoreModel):
    """
    Representa las reseñas de los productos.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.CharField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)


    def __str__(self):
        return self.subject


class ProductGallery(CoreModel):
    """
    Representa la galería de imágenes para un producto.
    """
    product = models.ForeignKey(
        Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=gallery_image_path, max_length=255)

    def __str__(self):
        return self.product.product_name
