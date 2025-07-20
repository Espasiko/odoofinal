/**
 * Funcionalidad para la barra lateral de categorías
 * Maneja el toggle en dispositivos móviles
 */

(function() {
    'use strict';

    // Esperar a que el DOM esté cargado
    document.addEventListener('DOMContentLoaded', function() {
        // Dar tiempo a Odoo para renderizar completamente
        setTimeout(initCategoriesToggle, 500);
    });

    /**
     * Inicializa la funcionalidad del toggle de categorías
     */
    function initCategoriesToggle() {
        const toggleBtn = document.querySelector('.categories-toggle');
        const sidebar = document.querySelector('.categories-sidebar');
        
        if (!toggleBtn || !sidebar) {
            console.log('Elementos de categorías no encontrados, reintentando...');
            // Reintentar después de un tiempo
            setTimeout(initCategoriesToggle, 1000);
            return;
        }

        console.log('Inicializando toggle de categorías');

        // Manejar click en el botón toggle
        toggleBtn.addEventListener('click', function() {
            toggleCategories(toggleBtn, sidebar);
        });

        // Cerrar sidebar al hacer click fuera en móviles
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 992) { // Cambiado a 992px para coincidir con Bootstrap lg
                if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                    closeCategories(toggleBtn, sidebar);
                }
            }
        });

        // Manejar cambios de tamaño de ventana
        window.addEventListener('resize', function() {
            handleResize(toggleBtn, sidebar);
        });
    }

    /**
     * Alterna la visibilidad de las categorías
     */
    function toggleCategories(toggleBtn, sidebar) {
        const isVisible = sidebar.classList.contains('show');
        
        if (isVisible) {
            closeCategories(toggleBtn, sidebar);
        } else {
            openCategories(toggleBtn, sidebar);
        }
    }

    /**
     * Abre el panel de categorías
     */
    function openCategories(toggleBtn, sidebar) {
        sidebar.classList.add('show');
        toggleBtn.classList.add('active');
        
        // Cambiar texto del botón
        const btnText = toggleBtn.querySelector('.btn-text');
        if (btnText) {
            btnText.textContent = 'Ocultar Categorías';
        }
        
        // Scroll suave hacia las categorías
        setTimeout(() => {
            sidebar.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
    }

    /**
     * Cierra el panel de categorías
     */
    function closeCategories(toggleBtn, sidebar) {
        sidebar.classList.remove('show');
        toggleBtn.classList.remove('active');
        
        // Cambiar texto del botón
        const btnText = toggleBtn.querySelector('.btn-text');
        if (btnText) {
            btnText.textContent = 'Ver Categorías';
        }
    }

    /**
     * Maneja los cambios de tamaño de ventana
     */
    function handleResize(toggleBtn, sidebar) {
        if (window.innerWidth > 768) {
            // En desktop, mostrar sidebar y ocultar botón
            sidebar.classList.remove('show');
            toggleBtn.classList.remove('active');
            sidebar.style.display = '';
        } else {
            // En móvil, manejar visibilidad con clases
            if (!sidebar.classList.contains('show')) {
                sidebar.style.display = 'none';
            }
        }
    }

    /**
     * Añade efectos de hover mejorados
     */
    function enhanceHoverEffects() {
        const categoryItems = document.querySelectorAll('.category-item');
        
        categoryItems.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.style.transform = 'translateX(8px)';
            });
            
            item.addEventListener('mouseleave', function() {
                this.style.transform = 'translateX(0)';
            });
        });
    }

    // Inicializar efectos adicionales cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        enhanceHoverEffects();
    });

})();