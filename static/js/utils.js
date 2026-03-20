/**
 * Utilidades JavaScript para el Sistema de Beneficios
 */

document.addEventListener('DOMContentLoaded', function() {
    initLoadingIndicators();
    initLocalStorageFilters();
    initFormValidation();
});

/**
 * Inicializa indicadores de carga para formularios y botones
 */
function initLoadingIndicators() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                showLoading(submitBtn);
            }
        });
    });

    document.querySelectorAll('.btn-download, .btn-pdf, .btn-excel').forEach(btn => {
        btn.addEventListener('click', function(e) {
            showLoading(this);
        });
    });
}

/**
 * Muestra indicador de carga en un elemento
 */
function showLoading(element) {
    const originalText = element.innerHTML;
    element.setAttribute('data-original-text', originalText);
    element.disabled = true;
    element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Cargando...';
    element.classList.add('loading');
}

/**
 * Oculta indicador de carga
 */
function hideLoading(element) {
    const originalText = element.getAttribute('data-original-text');
    if (originalText) {
        element.innerHTML = originalText;
        element.disabled = false;
        element.removeAttribute('data-original-text');
        element.classList.remove('loading');
    }
}

/**
 * Inicializa persistencia de filtros en localStorage
 */
function initLocalStorageFilters() {
    const filterForms = document.querySelectorAll('[data-persist-filters]');
    
    filterForms.forEach(form => {
        const formId = form.id || form.action;
        
        const savedFilters = localStorage.getItem(`filters_${formId}`);
        if (savedFilters) {
            try {
                const filters = JSON.parse(savedFilters);
                Object.keys(filters).forEach(key => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.value = filters[key];
                    }
                });
            } catch (e) {
                console.warn('Error al cargar filtros guardados');
            }
        }
        
        form.addEventListener('change', function() {
            const filters = {};
            form.querySelectorAll('input, select').forEach(input => {
                if (input.name && input.value) {
                    filters[input.name] = input.value;
                }
            });
            localStorage.setItem(`filters_${formId}`, JSON.stringify(filters));
        });
        
        const clearBtn = form.querySelector('[data-clear-filters]');
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                localStorage.removeItem(`filters_${formId}`);
            });
        }
    });
}

/**
 * Inicializa validación de formularios
 */
function initFormValidation() {
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
    
    const cedulaInputs = document.querySelectorAll('[data-validate-cedula]');
    cedulaInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateCedula(this);
        });
    });
}

/**
 * Valida formulario completo
 */
function validateForm(form) {
    let isValid = true;
    form.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    return isValid;
}

/**
 * Valida formato de cédula venezolana
 */
function validateCedula(input) {
    const pattern = /^[VEve][0-9]{7,8}$/;
    const value = input.value.trim();
    
    if (value && !pattern.test(value)) {
        input.classList.add('is-invalid');
        input.setCustomValidity('La cédula debe tener formato V12345678 o E12345678');
        return false;
    } else {
        input.classList.remove('is-invalid');
        input.setCustomValidity('');
        return true;
    }
}

/**
 * Utilidad para mostrar notificaciones toast
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

/**
 * Crea contenedor de toasts si no existe
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1100';
    document.body.appendChild(container);
    return container;
}

/**
 * Debounce para optimizar búsquedas
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Filtro en tiempo real para tablas
 */
function initTableSearch() {
    const searchInputs = document.querySelectorAll('[data-table-search]');
    
    searchInputs.forEach(input => {
        const debouncedSearch = debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const tableId = input.getAttribute('data-table-search');
            const table = document.getElementById(tableId);
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            }
        }, 300);
        
        input.addEventListener('input', debouncedSearch);
    });
}

window.SistemaBeneficio = {
    showLoading,
    hideLoading,
    showToast,
    validateCedula,
    debounce
};
