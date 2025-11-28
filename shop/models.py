from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse


class TimeStampedModel(models.Model):
    """Abstract base class with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("catalog") + f"?category={self.slug}"


class Product(TimeStampedModel):
    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    main_image = models.ImageField(upload_to="products/main/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("0.0")
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("product_detail", args=[self.slug])

    @property
    def primary_image(self):
        """Return preferred image, falling back to gallery or None."""
        main = self.images.filter(is_main=True).first()
        if main:
            return main.image
        fallback = self.images.first()
        if fallback:
            return fallback.image
        return self.main_image


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=255, blank=True)
    is_main = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return f"{self.product.name} image"


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    def __str__(self) -> str:
        return f"Profile for {self.user}"


class Order(TimeStampedModel):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Ожидание"),
        (STATUS_PROCESSING, "В обработке"),
        (STATUS_SHIPPED, "Отправлен"),
        (STATUS_DELIVERED, "Доставлен"),
        (STATUS_CANCELLED, "Отменен"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk}"

    @property
    def total_amount(self) -> Decimal:
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["order_id"]

    def __str__(self) -> str:
        return f"{self.product} x {self.quantity}"

    @property
    def total_price(self) -> Decimal:
        return self.unit_price * self.quantity
