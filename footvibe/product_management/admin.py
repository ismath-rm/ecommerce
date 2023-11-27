from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(ProductVariant)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Attribute)
admin.site.register(Attribute_Value)
admin.site.register(Product)
admin.site.register(ProductImage)
