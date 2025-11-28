(function () {
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

    function handleCartForm(event) {
        const form = event.target;
        if (!form.classList.contains('js-cart-form')) {
            return;
        }
        event.preventDefault();
        const formData = new FormData(form);
        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then((data) => {
                updateCartSummary(data);
                if (form.dataset.refresh === 'true') {
                    window.location.reload();
                }
            })
            .catch(() => {
                form.submit();
            });
    }

    document.addEventListener('submit', handleCartForm);
})();

