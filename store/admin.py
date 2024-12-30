from django.contrib import admin
from .models import Product, Variation, VariationCategory, ReviewRating, ProductGallery
import admin_thumbnails

# Galería de imágenes para productos
@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


# Configuración de ProductAdmin para incluir galería y selección de variaciones
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}
    list_filter = ('category', 'is_available')
    search_fields = ('product_name', 'description')
    list_editable = ('is_available', 'stock', 'price')
    inlines = [ProductGalleryInline]

    # Mostrar variaciones asociadas en la vista de detalle del producto
    filter_horizontal = ('variations',)  # Campo de muchos a muchos


# Configuración de administración para categorías de variación
class VariationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# Configuración de administración para variaciones
class VariationAdmin(admin.ModelAdmin):
    list_display = ('variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('variation_category', 'is_active')
    search_fields = ('variation_value',)


# Configuración de administración para reseñas de productos
class ReviewRatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at', 'status')
    list_filter = ('status', 'rating', 'created_at')
    search_fields = ('subject', 'review', 'user__email')
    list_editable = ('status',)


# Registro de modelos en el admin
admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(VariationCategory, VariationCategoryAdmin)
admin.site.register(ReviewRating, ReviewRatingAdmin)
admin.site.register(ProductGallery)
