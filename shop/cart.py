from decimal import Decimal

from .models import Product


class Cart:
    """Session-backed cart implementation."""

    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[self.SESSION_KEY] = cart
        self.cart = cart

    def _save(self):
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def add(self, product_id: int, quantity: int = 1, replace: bool = False):
        product = Product.objects.get(pk=product_id, is_active=True)
        product_id = str(product_id)
        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}
        if replace:
            self.cart[product_id]["quantity"] = max(1, quantity)
        else:
            self.cart[product_id]["quantity"] += quantity
        self._save()
        return product

    def remove(self, product_id: int):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self._save()

    def clear(self):
        self.cart = {}
        self._save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = (
            Product.objects.filter(id__in=product_ids)
            .select_related("category")
            .prefetch_related("images")
        )
        product_map = {str(product.id): product for product in products}
        for pid, item in self.cart.items():
            product = product_map.get(pid)
            if not product:
                continue
            item_data = {
                "product": product,
                "quantity": item["quantity"],
                "price": Decimal(item["price"]),
            }
            item_data["total_price"] = item_data["price"] * item_data["quantity"]
            yield item_data

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    @property
    def total(self) -> Decimal:
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

