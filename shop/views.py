from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import (
    CheckoutForm,
    ProductSearchForm,
    ProfileForm,
    UserRegistrationForm,
)
from .models import Category, Order, OrderItem, Product, UserProfile


def home(request):
    base_qs = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
    )
    featured_products = base_qs.filter(is_featured=True)[:8]
    new_arrivals = base_qs.order_by("-created_at")[:8]
    categories = Category.objects.all()
    return render(
        request,
        "home.html",
        {
            "featured_products": featured_products,
            "new_arrivals": new_arrivals,
            "categories": categories,
        },
    )


def category_list(request):
    categories = Category.objects.all()
    return render(request, "catalog/categories.html", {"categories": categories})


def catalog(request):
    category_slug = request.GET.get("category")
    search_query = request.GET.get("q", "")
    sort_mode = request.GET.get("sort")
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
    )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    if sort_mode == "new":
        products = products.order_by("-created_at")
    else:
        products = products.order_by("name")

    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    search_form = ProductSearchForm(initial={"q": search_query})

    return render(
        request,
        "catalog/catalog.html",
        {
            "page_obj": page_obj,
            "categories": categories,
            "active_category": category_slug,
            "active_sort": sort_mode,
            "search_form": search_form,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images"),
        slug=slug,
        is_active=True,
    )
    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)
        .select_related("category")
        .prefetch_related("images")[:4]
    )

    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "related_products": related_products,
            "gallery": product.images.all(),
        },
    )


def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/cart_detail.html", {"cart": cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    quantity = int(request.POST.get("quantity", 1))
    product = cart.add(product_id, quantity=quantity)
    messages.success(request, f"{product.name} добавлен в корзину.")
    return _cart_response(request, cart)


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    quantity = int(request.POST.get("quantity", 1))
    cart.add(product_id, quantity=quantity, replace=True)
    return _cart_response(request, cart)


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    return _cart_response(request, cart)


def _cart_response(request, cart):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "items": len(cart),
                "total": f"{cart.total:.2f}",
            }
        )
    return redirect("cart_detail")


@login_required
def account_dashboard(request):
    user_orders = request.user.orders.all()
    orders = user_orders.prefetch_related("items__product")[:5]
    stats = user_orders.aggregate(
        total_spent_value=Sum(F("items__unit_price") * F("items__quantity"))
    )
    total_spent = stats["total_spent_value"] or Decimal("0")
    orders_count = user_orders.count()
    return render(
        request,
        "account/dashboard.html",
        {"orders": orders, "total_spent": total_spent, "orders_count": orders_count},
    )


@login_required
def account_orders(request):
    orders = request.user.orders.prefetch_related("items__product")
    return render(request, "account/orders.html", {"orders": orders})


@login_required
def account_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлен.")
            return redirect("account_profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "account/profile.html", {"form": form})


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Добро пожаловать в GreenShop!")
            return redirect("home")
    else:
        form = UserRegistrationForm()
    return render(request, "registration/register.html", {"form": form})


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Корзина пуста.")
        return redirect("catalog")

    initial = {}
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        initial = {
            "first_name": request.user.first_name or "",
            "last_name": request.user.last_name or "",
            "email": request.user.email,
            "phone": profile.phone,
            "address": profile.address,
            "city": profile.city,
            "postal_code": profile.postal_code,
        }

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                order.save()
                items = [
                    OrderItem(
                        order=order,
                        product=item["product"],
                        quantity=item["quantity"],
                        unit_price=item["price"],
                    )
                    for item in cart
                ]
                OrderItem.objects.bulk_create(items)
            cart.clear()
            messages.success(request, "Заказ оформлен.")
            return redirect("order_confirmation", pk=order.pk)
    else:
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "order/checkout.html",
        {"cart": cart, "form": form},
    )


def order_confirmation(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"), pk=pk
    )
    if order.user and order.user != request.user:
        messages.error(request, "Нет доступа к заказу.")
        return redirect("home")
    return render(request, "order/confirmation.html", {"order": order})
