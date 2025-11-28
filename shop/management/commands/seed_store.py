from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from shop.models import Category, Product


class Command(BaseCommand):
    help = "Наполняет магазин тестовыми категориями и товарами."

    def handle(self, *args, **options):
        categories = [
            ("Органические продукты", "Все самое свежее и экологичное."),
            ("Косметика", "Натуральные средства по уходу."),
            ("Дом и интерьер", "Товары для уютного и эко-дома."),
            ("Спорт и активный отдых", "Снаряжение и одежда."),
        ]

        category_map = {}
        for name, description in categories:
            slug = slugify(name)
            category, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": description},
            )
            category_map[slug] = category

        products = [
            {
                "name": "Эко набор для кухни",
                "category": "Дом и интерьер",
                "price": Decimal("2499.00"),
                "description": "Комплект бамбуковой посуды и льняных салфеток.",
                "is_featured": True,
            },
            {
                "name": "Набор органических специй",
                "category": "Органические продукты",
                "price": Decimal("1099.00"),
                "description": "Ароматные специи без усилителей вкуса.",
                "is_featured": True,
            },
            {
                "name": "Веганский крем для лица",
                "category": "Косметика",
                "price": Decimal("1890.00"),
                "description": "Легкий увлажняющий крем на растительной основе.",
                "is_featured": True,
            },
            {
                "name": "Термос из переработанной стали",
                "category": "Спорт и активный отдых",
                "price": Decimal("1590.00"),
                "description": "Держит температуру до 12 часов, подходит для походов.",
                "is_featured": False,
            },
            {
                "name": "Бамбуковая зубная щётка",
                "category": "Косметика",
                "price": Decimal("290.00"),
                "description": "Разлагаемая щетка с мягкой щетиной.",
                "is_featured": False,
            },
            {
                "name": "Набор многоразовых мешочков",
                "category": "Дом и интерьер",
                "price": Decimal("590.00"),
                "description": "Удобно для покупок и хранения продуктов.",
                "is_featured": False,
            },
        ]

        created = 0
        for data in products:
            category = category_map.get(slugify(data["category"]))
            if not category:
                continue
            product, was_created = Product.objects.get_or_create(
                slug=slugify(data["name"]),
                defaults={
                    "name": data["name"],
                    "category": category,
                    "description": data["description"],
                    "price": data["price"],
                    "stock": 50,
                    "is_featured": data["is_featured"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Готово! Добавлено {created} новых товаров и {len(category_map)} категорий.")
        )

