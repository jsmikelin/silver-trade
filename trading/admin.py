from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Customer, Inquiry, Order, Blog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name_en", "category", "purity", "moq", "is_active", "sort_order"]
    list_filter = ["category", "is_active"]
    search_fields = ["name_en", "name_cn"]
    list_editable = ["is_active", "sort_order"]

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["company_name", "contact_person", "email", "phone", "country", "market", "created_at"]
    list_filter = ["market", "country"]
    search_fields = ["company_name", "contact_person", "email"]
    date_hierarchy = "created_at"

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "product", "quantity", "status", "created_at", "status_badge"]
    list_filter = ["status", "created_at"]
    search_fields = ["customer__company_name", "message"]
    list_editable = ["status"]
    date_hierarchy = "created_at"
    def status_badge(self, obj):
        colors = {"new":"red","quoted":"orange","negotiating":"blue","converted":"green","closed":"gray"}
        c = colors.get(obj.status, "gray")
        return format_html("<span style='color:{};font-weight:bold'>{}</span>", c, obj.get_status_display())
    status_badge.short_description = "状态"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_no", "customer", "product", "quantity", "total_amount", "status", "payment_term", "etd", "eta"]
    list_filter = ["status", "payment_term"]
    search_fields = ["order_no", "customer__company_name"]
    date_hierarchy = "created_at"
    readonly_fields = ["order_no", "created_at"]

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ["title_en", "category", "is_published", "published_at"]
    list_filter = ["is_published", "category"]
    search_fields = ["title_en", "title_jp"]
    date_hierarchy = "published_at"
