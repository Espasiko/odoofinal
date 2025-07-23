// Funcionalidades para el tema El Pelotazo
document.addEventListener('DOMContentLoaded', function() {
    // Actualizar cantidad del carrito
    function updateCartQuantity() {
        fetch('/shop/cart/quantity')
            .then(response => response.json())
            .then(data => {
                const cartQuantity = document.querySelector('.my_cart_quantity');
                if (cartQuantity) {
                    cartQuantity.textContent = data.quantity || '';
                    cartQuantity.style.display = data.quantity > 0 ? 'inline-block' : 'none';
                }
            });
    }

    // Actualizar carrito al agregar productos
    document.body.addEventListener('click', function(e) {
        if (e.target.closest('a[href*="/shop/cart/update"]')) {
            setTimeout(updateCartQuantity, 500);
        }
    });

    // Smooth scroll para enlaces internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Inicializar cantidad del carrito
    updateCartQuantity();
});

// Efecto de scroll en el header
window.addEventListener('scroll', function() {
    const header = document.querySelector('header');
    if (window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});
