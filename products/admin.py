from django.contrib import admin
from .models import Product, Category, Brand

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'brand', 'stock', 'is_active')
    list_filter = ('category', 'brand', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('image_tag',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'price', 'category', 'brand', 'stock', 'is_active', 'image', 'image_tag')
        }),
    )

    def image_tag(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height:100px;" />'
        return ""
    image_tag.short_description = 'Image Preview'
    image_tag.allow_tags = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    search_fields = ('name',)
