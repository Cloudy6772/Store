from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Order, UserProfile


class BootstrapFormMixin:
    """Добавляет Bootstrap-классы к вводу."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()


class ProductSearchForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(
        required=False,
        label="Поиск",
        widget=forms.TextInput(attrs={"placeholder": "Поиск товара"}),
    )


class CartUpdateForm(BootstrapFormMixin, forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99)


class CheckoutForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "city",
            "postal_code",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class UserRegistrationForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password1", "password2")


class StyledAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    """Авторизация с Bootstrap-оформлением."""


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "address", "city", "postal_code"]

