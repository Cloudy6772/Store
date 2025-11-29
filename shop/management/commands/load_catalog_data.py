import json
from decimal import Decimal
from pathlib import Path

from django.core.management import BaseCommand
from django.db import transaction

from shop.models import Category, Product


class Command(BaseCommand):
    help = "Загружает демонстрационные категории и товары из фикстур."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Удалить текущие категории и товары перед загрузкой.",
        )

    def handle(self, *args, **options):
        fixtures_dir = Path(__file__).resolve().parents[2] / "fixtures"
        categories_fixture = fixtures_dir / "catalog_categories.json"
        products_fixture = fixtures_dir / "catalog_products.json"

        if not categories_fixture.exists() or not products_fixture.exists():
            self.stderr.write("Фикстуры категорий или товаров не найдены.")
            return

        with open(categories_fixture, encoding="utf-8") as fh:
            categories_data = json.load(fh)
        with open(products_fixture, encoding="utf-8") as fh:
            products_data = json.load(fh)

        with transaction.atomic():
            if options["flush"]:
                self.stdout.write("Удаляем существующие товары и категории...")
                Product.objects.all().delete()
                Category.objects.all().delete()

            created_categories = self._load_categories(categories_data)
            created_products = self._load_products(products_data)

        self.stdout.write(
            self.style.SUCCESS(
                f"Загружено категорий: {created_categories}, товаров: {created_products}"
            )
        )

    def _load_categories(self, data):
        created = 0
        for entry in data:
            fields = entry["fields"]
            _, was_created = Category.objects.update_or_create(
                id=entry["pk"],
                defaults={
                    "name": fields["name"],
                    "slug": fields["slug"],
                    "description": fields.get("description", ""),
                    "image_url": fields.get("image_url", ""),
                },
            )
            if was_created:
                created += 1
        return created

    def _load_products(self, data):
        created = 0
        for entry in data:
            fields = entry["fields"]
            category_id = fields["category"]
            category = Category.objects.filter(pk=category_id).first()
            if not category:
                continue
            _, was_created = Product.objects.update_or_create(
                id=entry["pk"],
                defaults={
                    "category": category,
                    "name": fields["name"],
                    "slug": fields["slug"],
                    "description": fields.get("description", ""),
                    "price": Decimal(str(fields["price"])),
                    "stock": fields.get("stock", 0),
                    "image_url": fields.get("image_url", ""),
                    "is_active": fields.get("is_active", True),
                    "is_featured": fields.get("is_featured", False),
                    "rating": Decimal(str(fields.get("rating", "4.50"))),
                },
            )
            if was_created:
                created += 1
        return created

