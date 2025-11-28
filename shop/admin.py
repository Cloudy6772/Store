from django.contrib import admin
from django.db.models import F, Sum
from django.utils.safestring import mark_safe

from .models import Category, Order, OrderItem, Product, ProductImage, UserProfile


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "alt_text", "is_main", "display_order")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="80" height="80">')
        return "—"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "is_featured")
    list_filter = ("category", "is_active", "is_featured")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
    list_editable = ("price", "stock", "is_active", "is_featured")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "line_total")

    def line_total(self, obj):
        if not obj.pk:
            return "—"
        return f"{obj.total_price:.2f} ₽"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "user", "status", "total_amount_display")
    list_filter = ("status", "created_at")
    search_fields = ("first_name", "last_name", "email", "phone")
    inlines = [OrderItemInline]
    readonly_fields = ("created_at", "updated_at", "total_amount_display")
    change_list_template = "admin/shop/order/change_list.html"

    def total_amount_display(self, obj):
        return f"{obj.total_amount:.2f} ₽"

    total_amount_display.short_description = "Сумма"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, "context_data"):
            changelist = response.context_data.get("cl")
            if changelist:
                queryset = changelist.queryset
                stats = queryset.aggregate(
                    total_revenue=Sum(F("items__unit_price") * F("items__quantity")),
                    items_sold=Sum("items__quantity"),
                )
                response.context_data["sales_stats"] = {
                    "orders": queryset.count(),
                    "revenue": stats["total_revenue"] or 0,
                    "items": stats["items_sold"] or 0,
                }
        return response


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "city", "updated_at")
    search_fields = ("user__username", "phone", "city")
