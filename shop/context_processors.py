from .cart import Cart


def cart_summary(request):
    """Expose cart totals in all templates."""
    cart = Cart(request)
    return {
        "cart_item_count": len(cart),
        "cart_total_amount": cart.total,
    }

