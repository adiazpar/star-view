// Review System Component
window.ReviewSystem = (function() {
    'use strict';
    
    let config = {};
    let eventBus = null;
    
    // Initialize the review system
    function init(pageConfig, bus) {
        config = pageConfig;
        eventBus = bus;
        
        initializeReviewForm();
        initializeStarRating();
        initializeReviewFormToggle();
        setupEventListeners();
        setupOutsideClickHandler();
        calculateRatingDistribution();
        
        // Initialize after a short delay to ensure DOM is ready
        setTimeout(calculateRatingDistribution, 100);
    }
    
    // Initialize review form if user can write a review
    function initializeReviewForm() {
        if (config.isAuthenticated && !config.userHasReviewed && !config.isOwner) {
            const formContainer = document.getElementById('reviewFormContainer');
            if (formContainer) {
                const reviewForm = createReviewForm();
                if (reviewForm) {
                    formContainer.innerHTML = reviewForm.innerHTML;
                    
                    // Initialize contenteditable event listeners
                    const commentInput = formContainer.querySelector('.comment-input');
                    const hiddenInput = formContainer.querySelector('.hidden-content');
                    
                    if (commentInput && hiddenInput) {
                        // Set initial empty state
                        hiddenInput.value = '';
                        
                        // Add placeholder behavior
                        commentInput.addEventListener('focus', function() {
                            if (this.textContent.trim() === '' && !this.querySelector('*')) {
                                this.textContent = '';
                            }
                        });
                        
                        commentInput.addEventListener('blur', function() {
                            if (this.textContent.trim() === '' && !this.querySelector('*')) {
                                this.innerHTML = '';
                            }
                        });
                        
                        // Update hidden input on content change
                        commentInput.addEventListener('input', function() {
                            updateHiddenInput(this);
                        });
                    }
                    
                    // Add cancel button functionality
                    const cancelButton = formContainer.querySelector('.cancel-review');
                    if (cancelButton) {
                        cancelButton.addEventListener('click', function() {
                            handleCancelReview();
                        });
                    }
                }
            }
        }
    }
    
    // Function to create a review form from the template
    function createReviewForm() {
        const template = document.getElementById('reviewFormTemplate');
        if (!template) {
            console.error('Review form template not found');
            return null;
        }
        
        // Clone the template content
        const formContent = template.cloneNode(true);
        formContent.style.display = ''; // Remove the display: none
        formContent.id = ''; // Remove the ID to avoid duplicates
        
        // Update the CSRF token in the cloned form
        const csrfInput = formContent.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            csrfInput.value = config.csrfToken;
        }
        
        // Generate unique IDs for the star inputs to avoid conflicts
        const starInputs = formContent.querySelectorAll('.star-rating input[type="radio"]');
        const starLabels = formContent.querySelectorAll('.star-rating label');
        const uniqueId = Date.now(); // Use timestamp for uniqueness
        
        starInputs.forEach((input, index) => {
            const newId = `star${index + 1}-${uniqueId}`;
            input.id = newId;
            if (starLabels[index]) {
                starLabels[index].setAttribute('for', newId);
            }
        });
        
        // Update image upload element IDs to avoid conflicts
        const imageInput = formContent.querySelector('#review-images-input');
        const addImageBtn = formContent.querySelector('#add-image-btn');
        const previewContainer = formContent.querySelector('#image-preview-container');
        
        if (imageInput) {
            imageInput.id = `review-images-input-${uniqueId}`;
        }
        if (addImageBtn) {
            addImageBtn.id = `add-image-btn-${uniqueId}`;
        }
        if (previewContainer) {
            previewContainer.id = `image-preview-container-${uniqueId}`;
        }
        
        return formContent;
    }
    
    // Initialize star rating functionality
    function initializeStarRatingForContainer(container) {
        const labels = container.querySelectorAll('label');
        const inputs = container.querySelectorAll('input');
        
        // Handle hover effects
        labels.forEach((label, index) => {
            label.addEventListener('mouseover', function() {
                // Clear all hover states
                labels.forEach(l => l.classList.remove('hover'));
                // Add hover to current and all previous stars (left to right)
                for (let i = 0; i <= index; i++) {
                    labels[i].classList.add('hover');
                }
            });
            
            label.addEventListener('mouseout', function() {
                // Clear all hover states
                labels.forEach(l => l.classList.remove('hover'));
            });
            
            label.addEventListener('click', function() {
                const value = inputs[index].value;
                // Clear all filled states
                labels.forEach(l => l.classList.remove('filled'));
                // Fill stars from left to right up to selected value
                for (let i = 0; i < value; i++) {
                    labels[i].classList.add('filled');
                }
            });
        });
        
        // Handle input changes to maintain visual state
        inputs.forEach((input, index) => {
            input.addEventListener('change', function() {
                if (this.checked) {
                    const value = parseInt(this.value);
                    // Clear all filled states
                    labels.forEach(l => l.classList.remove('filled'));
                    // Fill stars from left to right up to selected value
                    for (let i = 0; i < value; i++) {
                        labels[i].classList.add('filled');
                    }
                }
            });
        });
    }

    function initializeStarRating() {
        const starContainers = document.querySelectorAll('.star-rating');
        
        starContainers.forEach(container => {
            initializeStarRatingForContainer(container);
        });
    }
    
    // Initialize review form toggle
    function initializeReviewFormToggle() {
        const toggleBtn = document.getElementById('toggleReviewForm');
        const formContainer = document.getElementById('reviewFormContainer');
        
        if (toggleBtn && formContainer) {
            toggleBtn.addEventListener('click', function() {
                // Don't allow interaction if button is disabled
                if (this.disabled || this.classList.contains('disabled')) {
                    return;
                }
                
                const isVisible = formContainer.style.display !== 'none';
                
                if (isVisible) {
                    formContainer.style.display = 'none';
                    toggleBtn.classList.remove('active');
                } else {
                    formContainer.style.display = 'block';
                    toggleBtn.classList.add('active');
                }
            });
        }
    }
    
    // Calculate and display rating distribution
    function calculateRatingDistribution() {
        const reviewCards = document.querySelectorAll('.review-card');
        const ratingCounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
        let totalReviews = 0;
        let totalRating = 0;
        
        // Count ratings from review cards
        reviewCards.forEach(card => {
            const filledStars = card.querySelectorAll('.rating-display svg.filled, .rating-display svg[style*="color: var(--golden)"]');
            const rating = filledStars.length;
            if (rating >= 1 && rating <= 5) {
                ratingCounts[rating]++;
                totalReviews++;
                totalRating += rating;
            }
        });
        
        // Get the metrics card
        const metricsCard = document.querySelector('.review-metrics-card');
        
        if (totalReviews === 0) {
            // Hide metrics card if no reviews
            if (metricsCard) {
                metricsCard.style.display = 'none';
            }
            return;
        }
        
        // Show metrics card if it was hidden
        if (metricsCard) {
            metricsCard.style.display = 'block';
        }
        
        // Calculate average rating
        const averageRating = totalRating / totalReviews;
        
        // Update overall rating number
        const ratingNumberElement = document.querySelector('.rating-number');
        if (ratingNumberElement) {
            ratingNumberElement.textContent = averageRating.toFixed(1);
        }
        
        // Update total reviews count
        const totalReviewsElement = document.querySelector('.total-reviews');
        if (totalReviewsElement) {
            const reviewText = totalReviews === 1 ? 'review' : 'reviews';
            totalReviewsElement.textContent = `${totalReviews} ${reviewText}`;
        }
        
        // Update star display with consistent styling
        const starContainer = document.querySelector('.rating-stars');
        if (starContainer) {
            const stars = starContainer.querySelectorAll('svg');
            const filledStars = Math.round(averageRating);
            
            stars.forEach((star, index) => {
                if (index < filledStars) {
                    star.style.color = 'var(--golden)';
                    star.style.fill = 'var(--golden)';
                } else {
                    star.style.color = 'var(--text-tertiary)';
                    star.style.fill = 'none'; // Consistent outline style for empty stars
                }
            });
        }
        
        // Update the rating bars and counts
        for (let star = 1; star <= 5; star++) {
            const count = ratingCounts[star];
            const percentage = totalReviews > 0 ? (count / totalReviews) * 100 : 0;
            
            const barFill = document.querySelector(`.rating-bar-fill[data-star="${star}"]`);
            const countElement = document.querySelector(`.rating-count[data-star-count="${star}"]`);
            
            if (barFill) {
                barFill.style.width = percentage + '%';
            }
            if (countElement) {
                const reviewText = count === 1 ? 'review' : 'reviews';
                countElement.textContent = `${count} ${reviewText}`;
            }
        }
    }
    
    // Setup event listeners for review actions
    function setupEventListeners() {
        const reviewsList = document.querySelector('.reviews-list');
        if (reviewsList) {
            reviewsList.addEventListener('click', handleReviewActions);
        }
    }
    
    // Handle review-related click events
    function handleReviewActions(e) {
        // Ellipsis menu button handling
        const ellipsisButton = e.target.closest('.ellipsis-menu-button');
        if (ellipsisButton) {
            e.preventDefault();
            e.stopPropagation();
            handleEllipsisMenu(ellipsisButton);
            return;
        }
        
        // Edit item in dropdown handling
        const editItem = e.target.closest('.edit-item');
        if (editItem) {
            e.preventDefault();
            e.stopPropagation();
            handleReviewEdit(editItem);
            return;
        }
        
        // Delete item in dropdown handling
        const deleteItem = e.target.closest('.delete-item');
        if (deleteItem) {
            e.preventDefault();
            e.stopPropagation();
            handleReviewDelete(deleteItem);
            return;
        }
    }
    
    // Handle ellipsis menu toggle
    function handleEllipsisMenu(ellipsisButton) {
        const reviewId = ellipsisButton.dataset.reviewId;
        const dropdown = document.querySelector(`.dropdown-menu[data-review-id="${reviewId}"]`);
        
        if (dropdown) {
            // Close all other dropdowns first
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                if (menu !== dropdown) {
                    menu.style.display = 'none';
                }
            });
            
            // Toggle current dropdown
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        }
    }
    
    // Handle review edit action
    function handleReviewEdit(editItem) {
        const reviewId = editItem.dataset.reviewId;
        
        // Find the review comment element to make editable
        const reviewElement = document.querySelector(`[data-review-id="${reviewId}"][data-editable="review"]`);
        
        if (reviewElement) {
            const originalContent = reviewElement.getAttribute('data-original-content');
            const ids = {
                locationId: config.locationId,
                reviewId: reviewId
            };
            
            // Use the editing system (will be moved to separate component later)
            if (window.EditingSystem) {
                window.EditingSystem.makeEditable(reviewElement, 'review', ids, originalContent);
            }
            
            // Close the dropdown menu
            const dropdown = editItem.closest('.dropdown-menu');
            if (dropdown) {
                dropdown.style.display = 'none';
            }
        }
    }
    
    // Handle review deletion
    function handleReviewDelete(deleteItem) {
        const reviewId = deleteItem.dataset.reviewId;
        
        if (confirm('Are you sure you want to delete your review?')) {
            fetch(`/delete-review/${reviewId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': config.csrfToken,
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) throw new Error('Failed to delete review');
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    handleSuccessfulDeletion(deleteItem, data);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to delete review. Please try again.');
            });
        }
    }
    
    // Handle successful review deletion
    function handleSuccessfulDeletion(deleteItem, data) {
        // Close the dropdown menu
        const dropdown = deleteItem.closest('.dropdown-menu');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
        
        // Remove the review card
        deleteItem.closest('.review-card').remove();

        // Check if there are any reviews left
        const reviewsList = document.querySelector('.reviews-list');
        if (!document.querySelector('.review-card')) {
            reviewsList.innerHTML = '<div class="no-reviews">No reviews yet</div>';
        }

        // Update the toggle button state if it exists
        updateToggleButtonAfterDeletion();

        // Update the existing review form container
        if (data.should_show_form) {
            setupReviewFormAfterDeletion();
        }
        
        // Recalculate and update the metrics card
        setTimeout(() => calculateRatingDistribution(), 100);
    }
    
    // Update toggle button after review deletion
    function updateToggleButtonAfterDeletion() {
        const toggleBtn = document.getElementById('toggleReviewForm');
        if (toggleBtn) {
            // Remove disabled state and class
            toggleBtn.disabled = false;
            toggleBtn.classList.remove('disabled', 'active');
            
            // Update button text
            const buttonSpan = toggleBtn.querySelector('span');
            if (buttonSpan) {
                buttonSpan.textContent = 'Write a Review';
            }
            
            // Update the icon from lock to pencil
            const currentIcon = toggleBtn.querySelector('svg');
            if (currentIcon) {
                const newIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-square-pen">
                    <path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/>
                </svg>`;
                currentIcon.outerHTML = newIcon;
            }
        }
    }
    
    // Setup review form after deletion
    function setupReviewFormAfterDeletion() {
        const existingFormContainer = document.getElementById('reviewFormContainer');
        if (existingFormContainer) {
            // Hide the container initially
            existingFormContainer.style.display = 'none';
            
            // Clear the container and add the cloned review form
            existingFormContainer.innerHTML = '';
            const newForm = createReviewForm();
            if (newForm) {
                // Extract just the inner content (not the wrapper div)
                existingFormContainer.innerHTML = newForm.innerHTML;
            }

            // Initialize star rating functionality
            setTimeout(() => {
                initializeStarRating();
                
                // Initialize comment formatting for the rich text editor
                const form = existingFormContainer.querySelector('.comment-form');
                if (form) {
                    const editableDiv = form.querySelector('.comment-input');
                    const hiddenInput = form.querySelector('.hidden-content');
                    
                    // Set up the placeholder behavior
                    if (editableDiv) {
                        editableDiv.addEventListener('focus', function() {
                            if (this.classList.contains('empty')) {
                                this.classList.remove('empty');
                                this.innerHTML = '';
                            }
                        });
                        
                        editableDiv.addEventListener('blur', function() {
                            if (this.innerHTML.trim() === '') {
                                this.classList.add('empty');
                                this.innerHTML = '';
                            }
                        });
                        
                        editableDiv.addEventListener('input', function() {
                            updateHiddenInput(this);
                        });
                        
                        // Initialize as empty
                        editableDiv.classList.add('empty');
                    }
                }
                
                // Add cancel button functionality
                const cancelButton = existingFormContainer.querySelector('.cancel-review');
                if (cancelButton) {
                    cancelButton.addEventListener('click', function() {
                        handleCancelReview();
                    });
                }
            }, 100);
        }
    }
    
    // Update hidden input with markdown content
    function updateHiddenInput(editableDiv) {
        const form = editableDiv.closest('.comment-form');
        const hiddenInput = form.querySelector('.hidden-content');
        
        // Convert HTML content to markdown for storage
        const htmlContent = editableDiv.innerHTML;
        const markdownContent = htmlToMarkdown(htmlContent);
        
        hiddenInput.value = markdownContent;
    }
    
    // Convert HTML to markdown
    function htmlToMarkdown(html) {
        // Create a temporary div to work with the HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // Process the HTML content to extract formatting
        const result = processNodeForMarkdown(tempDiv);
        
        return result.trim();
    }
    
    // Process HTML nodes for markdown conversion
    function processNodeForMarkdown(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node.textContent;
        }
        
        if (node.nodeType === Node.ELEMENT_NODE) {
            let content = '';
            
            // Process all child nodes first
            for (let child of node.childNodes) {
                content += processNodeForMarkdown(child);
            }
            
            // Apply formatting based on the current element
            const tagName = node.tagName ? node.tagName.toLowerCase() : '';
            
            switch (tagName) {
                case 'strong':
                case 'b':
                    return `**${content}**`;
                case 'em':
                case 'i':
                    return `*${content}*`;
                case 'u':
                    return `__${content}__`;
                case 'br':
                    return '\n';
                case 'div':
                    return content + '\n';
                default:
                    return content;
            }
        }
        
        return '';
    }
    
    // Handle cancel review action
    function handleCancelReview() {
        const formContainer = document.getElementById('reviewFormContainer');
        const toggleBtn = document.getElementById('toggleReviewForm');
        
        if (formContainer && toggleBtn) {
            // Clear the form
            const form = formContainer.querySelector('.review-form');
            if (form) {
                form.reset();
                
                // Clear star rating visual state
                const labels = form.querySelectorAll('.star-rating label');
                labels.forEach(label => label.classList.remove('filled'));
                
                // Clear comment input
                const commentInput = form.querySelector('.comment-input');
                const hiddenInput = form.querySelector('.hidden-content');
                if (commentInput) {
                    commentInput.innerHTML = '';
                }
                if (hiddenInput) {
                    hiddenInput.value = '';
                }
                
                // Clear any uploaded images
                if (window.ImageUploadSystem && window.ImageUploadSystem.clearAllImages) {
                    window.ImageUploadSystem.clearAllImages();
                }
            }
            
            // Hide the form container
            formContainer.style.display = 'none';
            
            // Update toggle button state
            toggleBtn.classList.remove('active');
        }
    }
    
    // Close dropdown when clicking outside
    function setupOutsideClickHandler() {
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.ellipsis-menu-wrapper')) {
                document.querySelectorAll('.dropdown-menu').forEach(menu => {
                    menu.style.display = 'none';
                });
            }
        });
    }
    
    // Public API
    return {
        init: init,
        calculateRatingDistribution: calculateRatingDistribution,
        initializeStarRatingForContainer: initializeStarRatingForContainer
    };
})();