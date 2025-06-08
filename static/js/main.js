/**
 * Main JavaScript file for SISIMPUR
 * Contains common functionality used across the application
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('SISIMPUR main.js loaded');
    
    // Initialize common functionality
    initializeCommonFeatures();
    
    // Handle Django messages
    handleDjangoMessages();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize form enhancements
    initializeFormEnhancements();
});

/**
 * Initialize common features across the application
 */
function initializeCommonFeatures() {
    // Add loading states to buttons
    const buttons = document.querySelectorAll('button[type="submit"], .btn-primary');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.form && !this.form.checkValidity()) {
                return;
            }
            
            // Add loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            this.disabled = true;
            
            // Reset after 5 seconds as fallback
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 5000);
        });
    });
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Handle Django messages and convert them to toasts
 */
function handleDjangoMessages() {
    const djangoMessages = document.querySelectorAll('.django-message');
    djangoMessages.forEach(function(messageEl) {
        const message = messageEl.textContent.trim();
        const type = messageEl.getAttribute('data-type') || 'info';
        const title = messageEl.getAttribute('data-title') || capitalizeFirstLetter(type);
        
        if (message && typeof window.showToast === 'function') {
            // Delay to ensure toast system is ready
            setTimeout(() => {
                window.showToast(type, title, message);
            }, 100);
        }
    });
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize form enhancements
 */
function initializeFormEnhancements() {
    // Add floating label effect
    const formInputs = document.querySelectorAll('.form-control, .form-select');
    formInputs.forEach(input => {
        // Add focus/blur handlers for floating labels
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Check if input has value on load
        if (input.value) {
            input.parentElement.classList.add('focused');
        }
    });
    
    // File input enhancements
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileCount = this.files.length;
            const label = this.nextElementSibling || this.parentElement.querySelector('label');
            
            if (label && fileCount > 0) {
                const fileNames = Array.from(this.files).map(file => file.name);
                if (fileCount === 1) {
                    label.textContent = fileNames[0];
                } else {
                    label.textContent = `${fileCount} files selected`;
                }
            }
        });
    });
}

/**
 * Utility function to capitalize first letter
 */
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Utility function to show loading overlay
 */
function showLoadingOverlay(message = 'Loading...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">${message}</p>
        </div>
    `;
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        color: white;
        text-align: center;
    `;
    
    document.body.appendChild(overlay);
    return overlay;
}

/**
 * Utility function to hide loading overlay
 */
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Make utility functions globally available
window.showLoadingOverlay = showLoadingOverlay;
window.hideLoadingOverlay = hideLoadingOverlay;
window.capitalizeFirstLetter = capitalizeFirstLetter;
