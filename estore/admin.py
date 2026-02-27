
from django.contrib import admin
from .models import Product, Cart, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "category", "price", "created_at")
	search_fields = ("name", "category")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "total_amount", "created_at")
	search_fields = ("user__username",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("id", "user_id", "total_amount", "payment_type", "status", "created_at", "completed_at")
	search_fields = ("user_id__username",)

# Register your models here.
