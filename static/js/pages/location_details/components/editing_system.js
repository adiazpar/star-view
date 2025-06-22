// Universal Editing System Component
window.EditingSystem = (function() {
    'use strict';
    
    let config = {};
    let eventBus = null;
    
    // Initialize the editing system
    function init(pageConfig, bus) {
        config = pageConfig;
        eventBus = bus;
    }
    
    // Make an element editable
    function makeEditable(element, type, ids, originalContent) {
        // Check if already in edit mode
        if (element.classList.contains('edit-mode')) {
            return; // Already editing, do nothing
        }
        
        // Hide the original content
        element.classList.add('edit-mode');
        
        // Hide original photos container for reviews to avoid duplication
        if (type === 'review') {
            const reviewCard = element.closest('.review-card');
            const originalPhotos = reviewCard ? reviewCard.querySelector('.review-photos') : null;
            if (originalPhotos) {
                originalPhotos.style.display = 'none';
                originalPhotos.setAttribute('data-hidden-for-edit', 'true');
            }
        }
        
        // Create edit controls container
        const editControls = document.createElement('div');
        editControls.className = 'edit-controls';
        
        // Generate star rating section for reviews
        const starRatingSection = type === 'review' ? `
            <div class="rating-input">
                <label>Rating:</label>
                <div class="star-rating" data-current-rating="">
                    <input type="radio" id="edit-star1-${ids.reviewId}" name="rating" value="1" required>
                    <label for="edit-star1-${ids.reviewId}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star filled">
                            <path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>
                        </svg>
                    </label>
                    <input type="radio" id="edit-star2-${ids.reviewId}" name="rating" value="2" required>
                    <label for="edit-star2-${ids.reviewId}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star filled">
                            <path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>
                        </svg>
                    </label>
                    <input type="radio" id="edit-star3-${ids.reviewId}" name="rating" value="3" required>
                    <label for="edit-star3-${ids.reviewId}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star filled">
                            <path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>
                        </svg>
                    </label>
                    <input type="radio" id="edit-star4-${ids.reviewId}" name="rating" value="4" required>
                    <label for="edit-star4-${ids.reviewId}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star filled">
                            <path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>
                        </svg>
                    </label>
                    <input type="radio" id="edit-star5-${ids.reviewId}" name="rating" value="5" required>
                    <label for="edit-star5-${ids.reviewId}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-star filled">
                            <path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z"/>
                        </svg>
                    </label>
                </div>
            </div>
        ` : '';

        // Generate image editing section for reviews
        const imageEditingSection = type === 'review' ? `
            <div class="review-images-input">
                <div class="image-upload-hint">You can upload up to 5 photos (JPEG, PNG, GIF)</div>
                <div class="image-upload-container">
                    <input type="file" 
                           name="review_images" 
                           id="edit-review-images-input-${ids.reviewId}" 
                           class="image-file-input" 
                           accept="image/*" 
                           multiple 
                           style="display: none;">
                    <div class="images-grid-container">
                        <div class="current-images-container" id="current-images-container-${ids.reviewId}">
                            <!-- Current images will be loaded here -->
                        </div>
                        <div class="image-preview-container" id="edit-image-preview-container-${ids.reviewId}"></div>
                        <button type="button" class="add-image-btn square" id="edit-add-image-btn-${ids.reviewId}">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                                <polyline points="21 15 16 10 5 21"></polyline>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        ` : '';
        
        editControls.innerHTML = `
            <div class="review-form">
                ${starRatingSection}
                <div class="review-comment-input">
                    <label for="comment">Comment:</label>
                    <div class="comment-form">
                        <div class="comment-input" 
                             contenteditable="true"
                             data-placeholder="Edit your ${type}..." 
                             data-name="content"></div>
                        <input type="hidden" name="content" class="hidden-content">
                        <div class="comment-toolbar">
                    <div class="comment-formatting-tools">
                        <button type="button" class="formatting-btn" title="Bold">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bold-icon lucide-bold"><path d="M6 12h9a4 4 0 0 1 0 8H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h7a4 4 0 0 1 0 8"/></svg>
                        </button>
                        <button type="button" class="formatting-btn" title="Italic">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-italic-icon lucide-italic"><line x1="19" x2="10" y1="4" y2="4"/><line x1="14" x2="5" y1="20" y2="20"/><line x1="15" x2="9" y1="4" y2="20"/></svg>
                        </button>
                        <button type="button" class="formatting-btn" title="Underline">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-underline-icon lucide-underline"><path d="M6 4v6a6 6 0 0 0 12 0V4"/><line x1="4" x2="20" y1="20" y2="20"/></svg>
                        </button>
                    </div>
                    <div class="edit-actions">
                        <button type="button" class="save-edit" data-type="${type}" data-ids='${JSON.stringify(ids)}'>
                            <i class="fas fa-check"></i>
                            Save
                        </button>
                        <button type="button" class="cancel-edit">
                            <i class="fas fa-times"></i>
                            Cancel
                        </button>
                        </div>
                    </div>
                </div>
                </div>
                ${imageEditingSection}
            </div>
        `;
        
        // Insert edit controls after the original element
        element.parentNode.insertBefore(editControls, element.nextSibling);
        
        // Pre-populate the editor with original markdown content converted to HTML
        const commentInput = editControls.querySelector('.comment-input');
        const hiddenInput = editControls.querySelector('.hidden-content');
        
        // Convert markdown to HTML for editing
        const htmlContent = markdownToHtml(originalContent);
        commentInput.innerHTML = htmlContent;
        hiddenInput.value = originalContent;
        
        // Set current rating for reviews
        if (type === 'review') {
            // Get current rating from data attribute
            let currentRating = parseInt(element.getAttribute('data-rating')) || 3;
            
            // Set the radio button and visual state
            const ratingInput = editControls.querySelector(`input[name="rating"][value="${currentRating}"]`);
            if (ratingInput) {
                ratingInput.checked = true;
                
                // Set visual state for star rating
                const starContainer = editControls.querySelector('.star-rating');
                const labels = starContainer.querySelectorAll('label');
                for (let i = 0; i < currentRating; i++) {
                    labels[i].classList.add('filled');
                }
            }
            
            // Initialize star rating functionality for the edit form
            setTimeout(() => {
                const starContainer = editControls.querySelector('.star-rating');
                if (starContainer && window.ReviewSystem) {
                    window.ReviewSystem.initializeStarRatingForContainer(starContainer);
                }
            }, 100);
            
            // Load current images for the review
            loadCurrentImages(ids.reviewId, ids.locationId);
            
            // Initialize image upload system for the edit form
            setTimeout(() => {
                if (window.ImageUploadSystem) {
                    // The ImageUploadSystem should work with the new edit form elements
                    console.log('Image upload system should be handling edit form elements');
                }
            }, 100);
        }
        
        // Focus the editor
        commentInput.focus();
        
        // Set up event handlers
        const saveBtn = editControls.querySelector('.save-edit');
        const cancelBtn = editControls.querySelector('.cancel-edit');
        
        saveBtn.addEventListener('click', function() {
            const newContent = hiddenInput.value.trim();
            
            // Get rating for reviews
            let rating = null;
            if (type === 'review') {
                const ratingInput = editControls.querySelector('input[name="rating"]:checked');
                if (ratingInput) {
                    rating = parseInt(ratingInput.value);
                }
            }
            
            // For reviews, allow saving with empty content as long as there's a rating
            // For comments, require content
            if (type === 'review' || newContent) {
                saveEdit(element, editControls, type, ids, newContent, rating);
            }
        });
        
        cancelBtn.addEventListener('click', function() {
            cancelEdit(element, editControls);
        });
    }
    
    // Convert markdown to HTML for editing
    function markdownToHtml(markdown) {
        if (!markdown) return '';
        
        // Enhanced markdown to HTML conversion with browser-compatible patterns
        let result = markdown;
        
        // Create unique placeholders for bold text to avoid conflicts
        const boldPlaceholders = [];
        result = result.replace(/\*\*(.*?)\*\*/g, function(match, content) {
            const placeholder = `__BOLD_${boldPlaceholders.length}__`;
            boldPlaceholders.push(content);
            return placeholder;
        });
        
        // Now handle italic (single asterisks)
        result = result.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>');
        
        // Restore bold text
        boldPlaceholders.forEach((content, index) => {
            result = result.replace(`__BOLD_${index}__`, `<strong>${content}</strong>`);
        });
        
        // Handle underline
        result = result.replace(/__(.*?)__/g, '<u>$1</u>');
        
        // Handle line breaks
        result = result.replace(/\n/g, '<br>');
        
        // Clean up multiple spaces
        result = result.replace(/  +/g, ' ');
        
        return result;
    }
    
    // Save edited content
    function saveEdit(element, editControls, type, ids, newContent, rating = null) {
        // Determine API endpoint based on type
        let endpoint;
        if (type === 'review') {
            endpoint = `/api/v1/viewing-locations/${ids.locationId}/reviews/${ids.reviewId}/`;
        } else if (type === 'comment') {
            endpoint = `/api/v1/viewing-locations/${ids.locationId}/reviews/${ids.reviewId}/comments/${ids.commentId}/`;
        }
        
        // Handle images for reviews
        let formData = null;
        let useFormData = false;
        
        if (type === 'review') {
            // Check if there are new images to upload or images to remove
            const fileInput = document.getElementById(`edit-review-images-input-${ids.reviewId}`);
            const hasNewImages = fileInput && fileInput.files.length > 0;
            const hasImagesToRemove = imagesToRemove.length > 0;
            
            if (hasNewImages || hasImagesToRemove) {
                useFormData = true;
                formData = new FormData();
                
                // Add text content and rating
                formData.append('comment', newContent);
                if (rating !== null) {
                    formData.append('rating', rating);
                }
                
                // Add new images
                if (hasNewImages) {
                    Array.from(fileInput.files).forEach((file, index) => {
                        formData.append('review_images', file);
                    });
                }
                
                // Add images to remove
                if (hasImagesToRemove) {
                    console.log('Images to remove:', imagesToRemove);
                    formData.append('remove_images', JSON.stringify(imagesToRemove));
                }
            }
        }
        
        // Prepare request body for non-image updates
        const requestBody = useFormData ? null : {
            [type === 'review' ? 'comment' : 'content']: newContent
        };
        
        // Add rating for reviews (non-FormData case)
        if (type === 'review' && rating !== null && !useFormData) {
            requestBody.rating = rating;
        }
        
        // Send update request
        const fetchOptions = {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': config.csrfToken
            },
            credentials: 'same-origin'
        };
        
        if (useFormData) {
            fetchOptions.body = formData;
            // Don't set Content-Type header for FormData, let browser set it
        } else {
            fetchOptions.headers['Content-Type'] = 'application/json';
            fetchOptions.body = JSON.stringify(requestBody);
        }
        
        fetch(endpoint, fetchOptions)
        .then(response => {
            if (!response.ok) {
                return response.json().then(error => {
                    throw new Error(error.detail || 'Failed to update');
                });
            }
            return response.json();
        })
        .then(data => {
            // Update the original element with new formatted content
            const contentField = type === 'review' ? 'comment' : 'content';
            // Prefer formatted_content from backend, fallback to markdown conversion
            const formattedContent = data.formatted_content || markdownToHtml(data[contentField]);
            element.innerHTML = formattedContent;
            
            // Update data attributes
            element.setAttribute('data-original-content', data[contentField]);
            
            // Update rating data attribute for reviews
            if (type === 'review' && data.rating) {
                element.setAttribute('data-rating', data.rating);
            }
            
            // Update star rating display for reviews
            if (type === 'review' && data.rating) {
                const reviewCard = element.closest('.review-card');
                const starElements = reviewCard.querySelectorAll('.rating-display svg');
                
                // Update star display with consistent styling
                starElements.forEach((star, index) => {
                    if (index < data.rating) {
                        star.style.color = 'var(--golden)';
                        star.style.fill = 'var(--golden)';
                        star.classList.add('filled');
                    } else {
                        star.style.color = 'var(--text-tertiary)';
                        star.style.fill = 'none'; // Ensure outline style for empty stars
                        star.classList.remove('filled');
                    }
                });
                
                // Notify review system to recalculate metrics
                if (eventBus) {
                    eventBus.emit('reviewUpdated', { reviewId: ids.reviewId, rating: data.rating });
                }
                
                // Fallback if no event bus
                if (window.ReviewSystem) {
                    setTimeout(() => window.ReviewSystem.calculateRatingDistribution(), 100);
                }
            }
            
            // Update photos for reviews if photos were modified
            if (type === 'review' && data.photos) {
                updateReviewPhotos(ids.reviewId, data.photos);
                
                // Clear the images to remove array
                imagesToRemove.length = 0;
            }
            
            // Clean up edit mode
            cancelEdit(element, editControls);
            
            // Emit update event
            if (eventBus) {
                eventBus.emit('contentUpdated', {
                    type: type,
                    id: type === 'review' ? ids.reviewId : ids.commentId,
                    data: data
                });
            }
        })
        .catch(error => {
            console.error('Error updating:', error);
            alert(`Failed to update ${type}. Please try again.`);
        });
    }
    
    // Cancel editing
    function cancelEdit(element, editControls) {
        // Remove edit controls
        editControls.remove();
        
        // Show original content
        element.classList.remove('edit-mode');
        
        // Restore original photos visibility for reviews
        const reviewCard = element.closest('.review-card');
        const originalPhotos = reviewCard ? reviewCard.querySelector('.review-photos[data-hidden-for-edit="true"]') : null;
        if (originalPhotos) {
            originalPhotos.style.display = '';
            originalPhotos.removeAttribute('data-hidden-for-edit');
        }
        
        // Clear images to remove array when canceling
        imagesToRemove.length = 0;
    }
    
    // Load current images for editing
    function loadCurrentImages(reviewId, locationId) {
        // Find the original review photos container
        const reviewCard = document.querySelector(`[data-review-id="${reviewId}"]`).closest('.review-card');
        const photosContainer = reviewCard ? reviewCard.querySelector('.review-photos') : null;
        
        if (photosContainer) {
            const currentImagesContainer = document.getElementById(`current-images-container-${reviewId}`);
            if (currentImagesContainer) {
                // Get all current photos
                const photoItems = photosContainer.querySelectorAll('.review-photo-item');
                
                // Set the image count attribute for CSS styling
                currentImagesContainer.setAttribute('data-image-count', photoItems.length);
                
                photoItems.forEach((photoItem, index) => {
                    const img = photoItem.querySelector('.review-photo-thumbnail');
                    const photoId = photoItem.dataset.photoId;
                    
                    if (img && photoId) {
                        const editablePhotoItem = document.createElement('div');
                        editablePhotoItem.className = 'editable-photo-item';
                        editablePhotoItem.innerHTML = `
                            <img src="${img.src}" alt="Review photo ${index + 1}" class="editable-photo-thumbnail">
                            <button type="button" class="remove-current-image-btn" data-photo-id="${photoId}" title="Remove image">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        `;
                        currentImagesContainer.appendChild(editablePhotoItem);
                    }
                });
            }
        }
    }
    
    // Update review photos display after edit
    function updateReviewPhotos(reviewId, photos) {
        const reviewCard = document.querySelector(`[data-review-id="${reviewId}"]`).closest('.review-card');
        const existingPhotosContainer = reviewCard ? reviewCard.querySelector('.review-photos') : null;
        
        if (photos.length === 0) {
            // Remove photos container if no photos
            if (existingPhotosContainer) {
                existingPhotosContainer.remove();
            }
        } else {
            // Update or create photos container
            let photosContainer = existingPhotosContainer;
            
            if (!photosContainer) {
                // Create new photos container
                photosContainer = document.createElement('div');
                photosContainer.className = 'review-photos';
                
                // Insert after review comment
                const commentElement = reviewCard.querySelector('.review-comment');
                if (commentElement) {
                    commentElement.parentNode.insertBefore(photosContainer, commentElement.nextSibling);
                }
            }
            
            // Update data attribute and rebuild photos
            photosContainer.setAttribute('data-image-count', photos.length);
            photosContainer.innerHTML = '';
            
            photos.forEach(photo => {
                const photoItem = document.createElement('div');
                photoItem.className = 'review-photo-item';
                photoItem.setAttribute('data-photo-id', photo.id);
                photoItem.innerHTML = `
                    <img src="${photo.thumbnail_url}" 
                         alt="Review photo"
                         class="review-photo-thumbnail"
                         data-full-url="${photo.image_url}"
                         loading="lazy">
                    ${photo.caption ? `<span class="photo-caption">${photo.caption}</span>` : ''}
                `;
                photosContainer.appendChild(photoItem);
            });
        }
    }
    
    // Track images to be removed
    let imagesToRemove = [];
    
    // Handle image removal in edit mode
    function handleImageRemoval() {
        document.addEventListener('click', function(e) {
            const removeBtn = e.target.closest('.remove-current-image-btn');
            if (removeBtn) {
                e.preventDefault();
                const photoId = removeBtn.dataset.photoId;
                const photoItem = removeBtn.closest('.editable-photo-item');
                
                if (photoId && photoItem) {
                    // Add to removal list
                    imagesToRemove.push(photoId);
                    
                    // Remove from UI
                    const container = photoItem.closest('.current-images-container');
                    photoItem.remove();
                    
                    // Update image count attribute
                    if (container) {
                        const remainingImages = container.querySelectorAll('.editable-photo-item').length;
                        container.setAttribute('data-image-count', remainingImages);
                    }
                    
                    // Update UI state
                    updateImageEditingUI();
                }
            }
        });
    }
    
    // Update image editing UI state
    function updateImageEditingUI() {
        // This function can be enhanced to update hints about image count limits
    }
    
    // Initialize image removal handler
    handleImageRemoval();
    
    // Public API
    return {
        init: init,
        makeEditable: makeEditable,
        getImagesToRemove: () => imagesToRemove,
        clearImagesToRemove: () => { imagesToRemove = []; }
    };
})();