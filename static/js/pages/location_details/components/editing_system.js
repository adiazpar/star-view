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
        
        // Prepare request body
        const requestBody = {
            [type === 'review' ? 'comment' : 'content']: newContent
        };
        
        // Add rating for reviews
        if (type === 'review' && rating !== null) {
            requestBody.rating = rating;
        }
        
        // Send update request
        fetch(endpoint, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': config.csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody),
            credentials: 'same-origin'
        })
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
    }
    
    // Public API
    return {
        init: init,
        makeEditable: makeEditable
    };
})();