// Image Upload System Component
window.ImageUploadSystem = (function() {
    'use strict';
    
    const MAX_IMAGES = 5;
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
    const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    
    let formFilesMap = new WeakMap(); // Store files per form
    
    // Initialize the image upload system
    function init() {
        setupImageUploadHandlers();
        setupLightbox();
    }
    
    // Helper functions for managing files per form
    function getFormFiles(form) {
        if (!formFilesMap.has(form)) {
            formFilesMap.set(form, []);
        }
        return formFilesMap.get(form);
    }
    
    function setFormFiles(form, files) {
        formFilesMap.set(form, files);
    }
    
    // Setup image upload handlers
    function setupImageUploadHandlers() {
        // Handle file input changes
        document.addEventListener('change', function(e) {
            if (e.target.matches('[id^="review-images-input"], [id^="edit-review-images-input"]')) {
                handleFileSelection(e.target);
            }
        });
        
        // Handle add image button clicks
        document.addEventListener('click', function(e) {
            const addBtn = e.target.closest('[id^="add-image-btn"], [id^="edit-add-image-btn"]');
            if (addBtn) {
                e.preventDefault();
                console.log('Add image button clicked:', addBtn.id);
                // Find the corresponding file input in the same form or edit controls
                const container = addBtn.closest('form') || addBtn.closest('.edit-controls');
                const input = container ? container.querySelector('[id^="review-images-input"], [id^="edit-review-images-input"]') : null;
                console.log('Found input:', input ? input.id : 'none');
                if (input) {
                    input.click();
                } else {
                    console.error('Could not find file input for add button');
                }
            }
            
            // Handle remove image button clicks
            if (e.target.closest('.remove-image-btn')) {
                e.preventDefault();
                const removeBtn = e.target.closest('.remove-image-btn');
                const index = parseInt(removeBtn.dataset.index);
                const form = removeBtn.closest('form');
                removeImage(index, form);
            }
            
            // Handle image thumbnail clicks for lightbox
            if (e.target.closest('.review-photo-thumbnail')) {
                e.preventDefault();
                const img = e.target.closest('.review-photo-thumbnail');
                openLightbox(img.dataset.fullUrl || img.src);
            }
        });
    }
    
    // Handle file selection
    function handleFileSelection(input) {
        const files = Array.from(input.files);
        const form = input.closest('form') || input.closest('.edit-controls');
        const container = form ? form.querySelector('[id^="image-preview-container"], [id^="edit-image-preview-container"]') : null;
        
        if (!container) {
            console.error('Could not find preview container');
            return;
        }
        
        // Get current files for this specific form
        const formFiles = getFormFiles(form);
        
        // Validate and process new files
        let validNewFiles = [];
        for (let file of files) {
            const validation = validateFile(file);
            if (validation.valid) {
                validNewFiles.push(file);
                // Stop if we would exceed the maximum
                if (formFiles.length + validNewFiles.length >= MAX_IMAGES) {
                    validNewFiles = validNewFiles.slice(0, MAX_IMAGES - formFiles.length);
                    break;
                }
            } else {
                showError(validation.error, form);
            }
        }
        
        // Add new files to existing files
        const allFiles = [...formFiles, ...validNewFiles];
        
        // Store all files for this form
        setFormFiles(form, allFiles);
        
        // Update file input with all files
        updateFileInput(input, allFiles);
        
        // Only display new files (append to existing display)
        displayNewPreviews(container, validNewFiles, formFiles.length);
        
        // Update UI state
        updateUploadUI(form, allFiles);
    }
    
    // Validate individual file
    function validateFile(file) {
        if (!ALLOWED_TYPES.includes(file.type)) {
            return { valid: false, error: `${file.name} is not a supported image type. Please use JPEG, PNG, or GIF.` };
        }
        
        if (file.size > MAX_FILE_SIZE) {
            return { valid: false, error: `${file.name} is too large. Maximum file size is 10MB.` };
        }
        
        return { valid: true };
    }
    
    // Update file input with new file list
    function updateFileInput(input, files) {
        // Create a new FileList-like object
        const dataTransfer = new DataTransfer();
        files.forEach(file => dataTransfer.items.add(file));
        input.files = dataTransfer.files;
    }
    
    // Display image previews (used for initial load and after removal)
    function displayPreviews(container, files) {
        container.innerHTML = '';
        files.forEach((file, index) => {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const previewItem = createPreviewElement(e.target.result, file.name, index);
                container.appendChild(previewItem);
            };
            
            reader.readAsDataURL(file);
        });
    }
    
    // Display only new image previews (append to existing)
    function displayNewPreviews(container, newFiles, startIndex) {
        newFiles.forEach((file, index) => {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const previewItem = createPreviewElement(e.target.result, file.name, startIndex + index);
                container.appendChild(previewItem);
            };
            
            reader.readAsDataURL(file);
        });
    }
    
    // Create preview element
    function createPreviewElement(src, filename, index) {
        const div = document.createElement('div');
        div.className = 'image-preview-item';
        div.innerHTML = `
            <img src="${src}" alt="${filename}" class="preview-image">
            <button type="button" class="remove-image-btn" data-index="${index}" title="Remove image">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;
        return div;
    }
    
    // Remove image from selection
    function removeImage(index, form) {
        const formFiles = getFormFiles(form);
        formFiles.splice(index, 1);
        
        const input = form.querySelector('[id^="review-images-input"], [id^="edit-review-images-input"]');
        const container = form.querySelector('[id^="image-preview-container"], [id^="edit-image-preview-container"]');
        
        if (input && container) {
            updateFileInput(input, formFiles);
            container.innerHTML = '';
            displayPreviews(container, formFiles);
            updateUploadUI(form, formFiles);
        }
    }
    
    // Update upload UI state
    function updateUploadUI(form, files) {
        const addBtn = form.querySelector('[id^="add-image-btn"], [id^="edit-add-image-btn"]');
        const hint = form.querySelector('.image-upload-hint');
        
        if (addBtn) {
            if (files.length >= MAX_IMAGES) {
                addBtn.style.display = 'none';
            } else {
                addBtn.style.display = 'flex';
                if (files.length > 0) {
                    const span = addBtn.querySelector('span');
                    if (span) {
                        span.textContent = `Add More (${MAX_IMAGES - files.length} left)`;
                    }
                }
            }
        }
        
        if (hint) {
            if (files.length > 0) {
                hint.textContent = `${files.length} of ${MAX_IMAGES} photos selected`;
            } else {
                hint.textContent = 'You can upload up to 5 photos (JPEG, PNG, GIF)';
            }
        }
    }
    
    // Setup lightbox functionality
    function setupLightbox() {
        // Create lightbox if it doesn't exist
        if (!document.getElementById('image-lightbox')) {
            const lightbox = document.createElement('div');
            lightbox.id = 'image-lightbox';
            lightbox.className = 'image-lightbox';
            lightbox.innerHTML = `
                <div class="lightbox-content">
                    <img src="" alt="Full size image" class="lightbox-image">
                    <button class="lightbox-close" title="Close">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
            `;
            document.body.appendChild(lightbox);
            
            // Close lightbox on click
            lightbox.addEventListener('click', function(e) {
                if (e.target === lightbox || e.target.closest('.lightbox-close')) {
                    closeLightbox();
                }
            });
            
            // Close on escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && lightbox.classList.contains('active')) {
                    closeLightbox();
                }
            });
        }
    }
    
    // Open lightbox with image
    function openLightbox(src) {
        const lightbox = document.getElementById('image-lightbox');
        const img = lightbox.querySelector('.lightbox-image');
        
        if (lightbox && img) {
            img.src = src;
            lightbox.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    // Close lightbox
    function closeLightbox() {
        const lightbox = document.getElementById('image-lightbox');
        if (lightbox) {
            lightbox.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Show error message
    function showError(message, form) {
        // Create a temporary error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'upload-error-message';
        errorDiv.textContent = message;
        
        const container = form.querySelector('.image-upload-container');
        if (container) {
            container.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    }
    
    // Reset image upload state for a specific form
    function resetForm(form) {
        if (!form) return;
        
        const formFiles = getFormFiles(form);
        formFiles.length = 0;
        
        const input = form.querySelector('[id^="review-images-input"], [id^="edit-review-images-input"]');
        const container = form.querySelector('[id^="image-preview-container"], [id^="edit-image-preview-container"]');
        
        if (input) input.value = '';
        if (container) container.innerHTML = '';
        
        updateUploadUI(form, []);
    }
    
    // Reset all forms
    function reset() {
        formFilesMap = new WeakMap();
        
        const inputs = document.querySelectorAll('[id^="review-images-input"], [id^="edit-review-images-input"]');
        const containers = document.querySelectorAll('[id^="image-preview-container"], [id^="edit-image-preview-container"]');
        
        inputs.forEach(input => input.value = '');
        containers.forEach(container => container.innerHTML = '');
    }
    
    // Public API
    return {
        init: init,
        reset: reset,
        resetForm: resetForm,
        getFormFiles: getFormFiles
    };
})();