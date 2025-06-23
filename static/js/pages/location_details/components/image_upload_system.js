// Image Upload System Component
window.ImageUploadSystem = (function() {
    'use strict';
    
    const MAX_IMAGES = 5;
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
    const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    
    let formFilesMap = new WeakMap(); // Store files per form
    let formExistingCountMap = new WeakMap(); // Store existing image count per form
    
    // Lightbox navigation state
    let currentPhotoIndex = 0;
    let currentReviewPhotos = [];
    
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
    
    // Helper functions for managing existing image count per form
    function getFormExistingCount(form) {
        return formExistingCountMap.get(form) || 0;
    }
    
    function setFormExistingCount(form, count) {
        formExistingCountMap.set(form, count);
    }
    
    // Setup image upload handlers
    function setupImageUploadHandlers() {
        // Handle file input changes  
        document.addEventListener('change', function(e) {
            // Check if it's an image file input for reviews
            if (e.target.type === 'file' && 
                e.target.accept && 
                e.target.accept.includes('image') &&
                (e.target.matches('[id^="review-images-input"], [id^="edit-review-images-input"]') ||
                 e.target.name === 'review_images')) {
                handleFileSelection(e.target);
            }
        });
        
        // Handle add image button clicks
        document.addEventListener('click', function(e) {
            const addBtn = e.target.closest('[id^="add-image-btn"], [id^="edit-add-image-btn"]');
            if (addBtn) {
                e.preventDefault();
                // Find the corresponding file input in the same form or edit controls
                const container = addBtn.closest('form') || addBtn.closest('.edit-controls');
                // Try multiple selection strategies to find the file input
                let input = null;
                if (container) {
                    // First try the standard selectors
                    input = container.querySelector('[id^="review-images-input"], [id^="edit-review-images-input"]');
                    
                    // If not found, try a more specific approach for edit mode
                    if (!input && addBtn.id.startsWith('edit-add-image-btn-')) {
                        const reviewId = addBtn.id.replace('edit-add-image-btn-', '');
                        input = container.querySelector(`#edit-review-images-input-${reviewId}`);
                    }
                    
                    // As a fallback, try finding any file input in the container
                    if (!input) {
                        input = container.querySelector('input[type="file"][accept*="image"]');
                    }
                }
                if (input) {
                    input.click();
                } else {
                    console.error('Could not find file input for add button:', addBtn.id);
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
                openLightbox(img.dataset.fullUrl || img.src, {
                    author: img.dataset.author,
                    authorAvatar: img.dataset.authorAvatar,
                    reviewDate: img.dataset.reviewDate,
                    locationName: img.dataset.locationName,
                    locationAddress: img.dataset.locationAddress
                });
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
        const existingCount = getFormExistingCount(form);
        const totalCurrentImages = existingCount + formFiles.length;
        
        // Validate and process new files
        let validNewFiles = [];
        for (let file of files) {
            const validation = validateFile(file);
            if (validation.valid) {
                // Check if we would exceed the maximum total images
                if (totalCurrentImages + validNewFiles.length >= MAX_IMAGES) {
                    // Silently limit to max allowed without showing error
                    validNewFiles = validNewFiles.slice(0, Math.max(0, MAX_IMAGES - totalCurrentImages));
                    break;
                }
                validNewFiles.push(file);
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
        const existingCount = getFormExistingCount(form);
        const totalImages = existingCount + files.length;
        
        if (addBtn) {
            if (totalImages >= MAX_IMAGES) {
                addBtn.style.display = 'none';
            } else {
                addBtn.style.display = 'flex';
                const remainingSlots = MAX_IMAGES - totalImages;
                const span = addBtn.querySelector('span');
                if (span) {
                    span.textContent = `Add More (${remainingSlots} left)`;
                }
            }
        }
        
        if (hint) {
            // Simple hint messages like the original form
            if (totalImages > 0) {
                hint.textContent = `${totalImages} of ${MAX_IMAGES} photos selected`;
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
                    <div class="lightbox-overlay">
                        <div class="lightbox-metadata">
                            <div class="lightbox-author">
                                <img src="" alt="Author avatar" class="author-avatar">
                                <div class="author-info">
                                    <span class="author-name"></span>
                                    <span class="lightbox-review-date"></span>
                                </div>
                            </div>
                            <div class="lightbox-location">
                                <div class="location-info">
                                    <span class="location-name"></span>
                                    <span class="location-address"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <button class="lightbox-close" title="Close">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                    <button class="lightbox-nav lightbox-prev" title="Previous photo">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="15,18 9,12 15,6"></polyline>
                        </svg>
                    </button>
                    <button class="lightbox-nav lightbox-next" title="Next photo">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="9,18 15,12 9,6"></polyline>
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
            
            // Navigation event listeners
            const prevBtn = lightbox.querySelector('.lightbox-prev');
            const nextBtn = lightbox.querySelector('.lightbox-next');
            
            prevBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                navigateLightbox(-1);
            });
            
            nextBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                navigateLightbox(1);
            });
            
            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (lightbox.classList.contains('active')) {
                    if (e.key === 'Escape') {
                        closeLightbox();
                    } else if (e.key === 'ArrowLeft') {
                        e.preventDefault();
                        navigateLightbox(-1);
                    } else if (e.key === 'ArrowRight') {
                        e.preventDefault();
                        navigateLightbox(1);
                    }
                }
            });
        }
    }
    
    // Navigate lightbox photos
    function navigateLightbox(direction) {
        if (currentReviewPhotos.length <= 1) return;
        
        const newIndex = currentPhotoIndex + direction;
        
        // Handle wrapping
        if (newIndex < 0) {
            currentPhotoIndex = currentReviewPhotos.length - 1;
        } else if (newIndex >= currentReviewPhotos.length) {
            currentPhotoIndex = 0;
        } else {
            currentPhotoIndex = newIndex;
        }
        
        // Update the lightbox with the new photo
        const photo = currentReviewPhotos[currentPhotoIndex];
        updateLightboxContent(photo.src, photo.metadata);
        updateNavigationState();
    }
    
    // Update navigation button states
    function updateNavigationState() {
        const lightbox = document.getElementById('image-lightbox');
        const prevBtn = lightbox.querySelector('.lightbox-prev');
        const nextBtn = lightbox.querySelector('.lightbox-next');
        
        if (currentReviewPhotos.length <= 1) {
            prevBtn.style.display = 'none';
            nextBtn.style.display = 'none';
        } else {
            prevBtn.style.display = 'flex';
            nextBtn.style.display = 'flex';
        }
    }
    
    // Update lightbox content
    function updateLightboxContent(src, metadata = {}) {
        const lightbox = document.getElementById('image-lightbox');
        const img = lightbox.querySelector('.lightbox-image');
        
        if (lightbox && img) {
            img.src = src;
            
            // Update metadata if provided
            if (metadata.author) {
                const authorName = lightbox.querySelector('.author-name');
                if (authorName) authorName.textContent = metadata.author;
            }
            
            if (metadata.authorAvatar) {
                const authorAvatar = lightbox.querySelector('.author-avatar');
                if (authorAvatar) authorAvatar.src = metadata.authorAvatar;
            }
            
            if (metadata.reviewDate) {
                const reviewDate = lightbox.querySelector('.lightbox-review-date');
                if (reviewDate) reviewDate.textContent = metadata.reviewDate;
            }
            
            if (metadata.locationName) {
                const locationName = lightbox.querySelector('.location-name');
                if (locationName) locationName.textContent = metadata.locationName;
            }
            
            if (metadata.locationAddress) {
                const locationAddress = lightbox.querySelector('.location-address');
                if (locationAddress) locationAddress.textContent = metadata.locationAddress;
            }
        }
    }
    
    // Open lightbox with image
    function openLightbox(src, metadata = {}) {
        const lightbox = document.getElementById('image-lightbox');
        const img = lightbox.querySelector('.lightbox-image');
        
        if (lightbox && img) {
            // Find all photos in the same review
            const clickedImg = document.querySelector(`img[data-full-url="${src}"], img[src="${src}"]`);
            if (clickedImg) {
                const reviewPhotosContainer = clickedImg.closest('.review-photos');
                if (reviewPhotosContainer) {
                    // Get all photos in this review
                    const allPhotos = reviewPhotosContainer.querySelectorAll('.review-photo-thumbnail');
                    currentReviewPhotos = Array.from(allPhotos).map(photo => ({
                        src: photo.dataset.fullUrl || photo.src,
                        metadata: {
                            author: photo.dataset.author,
                            authorAvatar: photo.dataset.authorAvatar,
                            reviewDate: photo.dataset.reviewDate,
                            locationName: photo.dataset.locationName,
                            locationAddress: photo.dataset.locationAddress
                        }
                    }));
                    
                    // Find the index of the clicked photo
                    currentPhotoIndex = currentReviewPhotos.findIndex(photo => photo.src === src);
                } else {
                    // Single photo, not part of a review collection
                    currentReviewPhotos = [{
                        src: src,
                        metadata: metadata
                    }];
                    currentPhotoIndex = 0;
                }
            } else {
                // Fallback for single photo
                currentReviewPhotos = [{
                    src: src,
                    metadata: metadata
                }];
                currentPhotoIndex = 0;
            }
            
            // Update the lightbox content
            updateLightboxContent(src, metadata);
            updateNavigationState();
            
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
        
        // Clear existing count for this form
        setFormExistingCount(form, 0);
        
        const input = form.querySelector('[id^="review-images-input"], [id^="edit-review-images-input"]');
        const container = form.querySelector('[id^="image-preview-container"], [id^="edit-image-preview-container"]');
        
        if (input) input.value = '';
        if (container) container.innerHTML = '';
        
        updateUploadUI(form, []);
    }
    
    // Reset all forms
    function reset() {
        formFilesMap = new WeakMap();
        formExistingCountMap = new WeakMap();
        
        const inputs = document.querySelectorAll('[id^="review-images-input"], [id^="edit-review-images-input"]');
        const containers = document.querySelectorAll('[id^="image-preview-container"], [id^="edit-image-preview-container"]');
        
        inputs.forEach(input => input.value = '');
        containers.forEach(container => container.innerHTML = '');
    }
    
    // Update UI with existing image count
    function updateUploadUIWithExisting(form, existingCount) {
        setFormExistingCount(form, existingCount);
        const files = getFormFiles(form);
        updateUploadUI(form, files);
    }
    
    // Public API
    return {
        init: init,
        reset: reset,
        resetForm: resetForm,
        getFormFiles: getFormFiles,
        updateUploadUIWithExisting: updateUploadUIWithExisting
    };
})();