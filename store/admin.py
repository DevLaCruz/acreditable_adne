from django.contrib import admin
from .models import Product, Variation, VariationCategory, ReviewRating, ProductGallery
import admin_thumbnails

# Register your models here.


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1
    fields = ('variation_category', 'variation_value', 'is_active')


class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category',
                    'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('product', 'variation_category',
                   'variation_value', 'is_active')


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock',
                    'category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}
    # Incluye la galería de productos y variaciones
    inlines = [ProductGalleryInline, VariationInline]


class VariationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(VariationCategory, VariationCategoryAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
