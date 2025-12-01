console.log("cart.js LOADED");

(function () {
    // debug = true покажет логи в консоли
    const debug = true;

    function log(...args) {
        if (debug && console && console.log) console.log("[cart.js]", ...args);
    }

    function getCsrfToken() {
        const name = 'csrftoken';
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return '';
    }

    function updateCartSummary(data) {
        const countEl = document.getElementById('cart-count');
        if (countEl && typeof data.items !== 'undefined') {
            countEl.textContent = data.items;
        }
        const totalEl = document.getElementById('cart-total');
        if (totalEl && typeof data.total !== 'undefined') {
            totalEl.textContent = data.total + ' ₽';
        }
    }

    function showToast(text) {
        try {
            const toastEl = document.getElementById('cart-toast');
            const toastTextEl = document.getElementById('cart-toast-text');
            if (!toastEl) {
                log("toast element not found");
                return;
            }
            if (toastTextEl && text) {
                toastTextEl.textContent = text;
            }
            // Используем getOrCreateInstance чтобы быть устойчивым к повторным вызовам
            const toast = (bootstrap && bootstrap.Toast)
                ? bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 5000 })
                : null;

            if (toast) {
                toast.show();
                log("toast shown via bootstrap.Toast");
            } else {
                // fallback: краткое всплывающее окно через alert (на случай, если bootstrap не доступен)
                log("bootstrap.Toast not available, falling back to alert");
                // eslint-disable-next-line no-alert
                alert(text || "Товар добавлен в корзину!");
            }
        } catch (err) {
            console.error("Error showing toast:", err);
        }
    }

    function handleCartForm(event) {
        const form = event.target;
        if (!form.classList.contains('js-cart-form')) {
            return;
        }
        event.preventDefault();

        // Отправляем форму через fetch (AJAX)
        const formData = new FormData(form);
        const action = form.action;

        log("Submitting cart form to", action);

        fetch(action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
            .then((response) => {
                log("fetch response ok:", response.ok, response.status);
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.status);
                }
                return response.json();
            })
            .then((data) => {
                log("AJAX response JSON:", data);
                updateCartSummary(data);

                // Показать уведомление — если сервер прислал product_name и quantity, используем их
                if (data.product_name || data.quantity) {
                    const name = data.product_name || '';
                    const qty = data.quantity || '';
                    const qtyText = qty ? ` (${qty} шт.)` : '';
                    showToast(`Добавлено: ${name}${qtyText}`);
                } else {
                    showToast("Товар добавлен в корзину!");
                }

                if (form.dataset.refresh === 'true') {
                    window.location.reload();
                }
            })
            .catch((err) => {
                console.error("Cart AJAX failed, falling back to normal submit:", err);
                // Если AJAX упал — отправляем форму обычным способом
                form.submit();
            });
    }

    // Ждём DOMContentLoaded — на всякий случай (если скрипт где-то подключён раньше)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            document.addEventListener('submit', handleCartForm);
            log("cart.js ready (DOMContentLoaded)");
        });
    } else {
        document.addEventListener('submit', handleCartForm);
        log("cart.js ready");
    }
})();
