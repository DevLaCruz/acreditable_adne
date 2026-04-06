from django.db import models
from django.urls import reverse
from core.models import CoreModel
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

def category_image_path(instance, filename):
    # store/category_name/filename
    return f'store/{instance.slug}/{filename}'

# Create your models here.
class Category(CoreModel):
    category_name=models.CharField(max_length=20, unique=True)
    description=models.CharField(max_length=255, blank=True)
    slug=models.CharField(max_length=100, unique=True)
    cat_image = models.ImageField(upload_to=category_image_path, blank=True)

    class Meta:
        verbose_name='category'
        verbose_name_plural='categories'

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.category_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Guarda la imagen original
        convert_to_webp(self, 'cat_image')  # Convierte a WebP