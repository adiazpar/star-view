// Consolidated Reviews Section JavaScript
// This file contains all the JavaScript components for the reviews section

// Shared Utilities
window.Utils = (function() {
    'use strict';
    
    // Remove HTML tags from a string
    function stripTags(str) {
        return str.replace(/<[^>]*>/g, '');
    }
    
    // Escape HTML entities to prevent XSS
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
    // Truncate text to a specific length
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }
    
    // Debounce function for performance optimization
    function debounce(func, wait, immediate) {
        let timeout;
        return function() {
            const context = this, args = arguments;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }
    
    // Check if an element is in viewport
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Smooth scroll to element
    function smoothScrollTo(element, offset = 0) {
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
    
    // Format number with commas (e.g., 1,234)
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    
    // Get query string parameter
    function getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }
    
    // Set query string parameter
    function setQueryParam(param, value) {
        const url = new URL(window.location);
        url.searchParams.set(param, value);
        window.history.pushState({}, '', url);
    }
    
    // Create loading spinner element
    function createLoadingSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = `
            <div class="spinner-border" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        `;
        return spinner;
    }
    
    // Show/hide loading state
    function toggleLoadingState(element, isLoading) {
        if (isLoading) {
            element.classList.add('loading');
            const spinner = createLoadingSpinner();
            element.appendChild(spinner);
        } else {
            element.classList.remove('loading');
            const spinner = element.querySelector('.loading-spinner');
            if (spinner) {
                spinner.remove();
            }
        }
    }
    
    // Throttle function for scroll events
    function throttle(func, delay) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, delay);
            }
        };
    }
    
    // Check if device is mobile
    function isMobile() {
        return window.innerWidth <= 768;
    }
    
    // Check if user prefers reduced motion
    function prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    
    // Generate unique ID
    function generateUniqueId(prefix = 'id') {
        return prefix + '-' + Math.random().toString(36).substr(2, 9);
    }
    
    // Public API
    return {
        stripTags: stripTags,
        escapeHtml: escapeHtml,
        truncateText: truncateText,
        debounce: debounce,
        isInViewport: isInViewport,
        smoothScrollTo: smoothScrollTo,
        formatNumber: formatNumber,
        getQueryParam: getQueryParam,
        setQueryParam: setQueryParam,
        createLoadingSpinner: createLoadingSpinner,
        toggleLoadingState: toggleLoadingState,
        throttle: throttle,
        isMobile: isMobile,
        prefersReducedMotion: prefersReducedMotion,
        generateUniqueId: generateUniqueId
    };
})();

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

                    if (commentInput) {
                        // Add placeholder behavior
                        commentInput.addEventListener('focus', function() {
                            if (this.textContent.trim() === '' && !this.querySelector('*')) {
                                this.textContent = '';
                            }
                        });

                        commentInput.addEventListener('blur', function() {
                            if (this.textContent.trim() === '' && !this.querySelector('*')) {
                                this.textContent = '';
                            }
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
        const imageInput = formContent.querySelector('#template-review-images-input');
        const addImageBtn = formContent.querySelector('#template-add-image-btn');
        const previewContainer = formContent.querySelector('#template-image-preview-container');
        
        if (imageInput) {
            imageInput.id = `review-images-input`;
        }
        if (addImageBtn) {
            addImageBtn.id = `add-image-btn`;
        }
        if (previewContainer) {
            previewContainer.id = `image-preview-container`;
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
            // Look for Font Awesome filled stars (fas) vs outline stars (far)
            const filledStars = card.querySelectorAll('.rating-display i.fas.fa-star');
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
        const editReviewItem = e.target.closest('.edit-review-item');
        if (editReviewItem) {
            e.preventDefault();
            e.stopPropagation();
            handleReviewEdit(editReviewItem);
            return;
        }
        
        // Delete item in dropdown handling
        const deleteReviewItem = e.target.closest('.delete-review-item');
        if (deleteReviewItem) {
            e.preventDefault();
            e.stopPropagation();
            handleReviewDelete(deleteReviewItem);
            return;
        }
        
        // Report item in dropdown handling
        const reportItem = e.target.closest('.report-item');
        if (reportItem) {
            e.preventDefault();
            e.stopPropagation();
            handleReviewReport(reportItem);
            return;
        }
    }
    
    // Handle ellipsis menu toggle
    function handleEllipsisMenu(ellipsisButton) {
        const reviewId = ellipsisButton.dataset.reviewId;
        const dropdown = document.querySelector(`.dropdown-menu[data-review-id="${reviewId}"]`);
        
        if (dropdown) {
            // Close all other dropdowns first (both review and comment dropdowns)
            document.querySelectorAll('.dropdown-menu[data-review-id], .dropdown-menu[data-comment-id]').forEach(menu => {
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
    
    // Handle review report action
    function handleReviewReport(reportItem) {
        const reviewId = reportItem.dataset.reviewId;
        
        // Close the dropdown menu
        const dropdown = reportItem.closest('.dropdown-menu');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
        
        // Open report modal
        if (window.ReportModal) {
            window.ReportModal.openModal('review', reviewId, config.locationId);
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

                    // Set up the placeholder behavior
                    if (editableDiv) {
                        editableDiv.addEventListener('focus', function() {
                            if (this.classList.contains('empty')) {
                                this.classList.remove('empty');
                                this.textContent = '';
                            }
                        });

                        editableDiv.addEventListener('blur', function() {
                            if (this.textContent.trim() === '') {
                                this.classList.add('empty');
                                this.textContent = '';
                            }
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
                if (commentInput) {
                    commentInput.textContent = '';
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
                document.querySelectorAll('.dropdown-menu[data-review-id]').forEach(menu => {
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

// Comment System Component
window.CommentSystem = (function() {
    'use strict';
    
    let config = {};
    let eventBus = null;
    
    // Initialize the comment system
    function init(pageConfig, bus) {
        config = pageConfig;
        eventBus = bus;

        setupEventListeners();
    }
    
    // Setup event listeners for comment functionality
    function setupEventListeners() {
        // Handle comment section toggling
        document.querySelectorAll('.comments-toggle').forEach(button => {
            button.addEventListener('click', function() {
                const reviewId = this.dataset.reviewId;
                const commentsContainer = document.getElementById(`comments-${reviewId}`);
                const isHidden = commentsContainer.style.display === 'none';

                commentsContainer.style.display = isHidden ? 'block' : 'none';
            });
        });

        // Handle comment submission
        document.querySelectorAll('.comment-form').forEach(form => {
            form.addEventListener('submit', handleCommentSubmission);
        });
        
        // Handle comment edit buttons and ellipsis menus
        const reviewsList = document.querySelector('.reviews-list');
        if (reviewsList) {
            reviewsList.addEventListener('click', handleCommentActions);
        }
        
        // Handle outside clicks to close comment dropdowns
        setupOutsideClickHandler();
    }
    
    // Handle comment form submission
    function handleCommentSubmission(e) {
        e.preventDefault();

        const reviewId = this.dataset.reviewId;
        const locationId = this.dataset.locationId;
        const commentInput = this.querySelector('.comment-input');

        // Get plain text content from contenteditable div or input
        let content;
        if (commentInput.contentEditable === 'true') {
            content = commentInput.textContent.trim();
        } else {
            content = commentInput.value.trim();
        }
        if (!content) return;

        fetch(`/api/viewing-locations/${locationId}/reviews/${reviewId}/comments/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': config.csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: content }),
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(error => {
                    throw new Error(error.detail || 'Failed to post comment');
                });
            }
            return response.json();
        })
        .then(data => {
            // Add the new comment to the list
            const commentsList = document.getElementById(`comments-list-${reviewId}`);
            const newComment = createCommentElement(data);
            commentsList.appendChild(newComment);

            // Clear the input
            if (commentInput.contentEditable === 'true') {
                commentInput.textContent = '';
            } else {
                commentInput.value = '';
            }

            // Update comment count in the voting controls
            const reviewCard = this.closest('.review-card');
            const countElement = reviewCard.querySelector('.comments-count');
            if (countElement) {
                const currentCount = parseInt(countElement.textContent);
                countElement.textContent = `${currentCount + 1} Comments`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to post comment. Please try again.');
        });
    }
    
    // Handle comment-related click events
    function handleCommentActions(e) {
        // Handle comment ellipsis menu buttons
        const ellipsisButton = e.target.closest('.ellipsis-menu-button[data-comment-id]');
        if (ellipsisButton) {
            e.preventDefault();
            e.stopPropagation();
            handleCommentEllipsisMenu(ellipsisButton);
            return;
        }
        
        // Handle dropdown menu actions
        const editCommentItem = e.target.closest('.edit-comment-item');
        const deleteCommentItem = e.target.closest('.delete-comment-item');
        const reportCommentItem = e.target.closest('.report-comment-item');
        
        if (editCommentItem || deleteCommentItem || reportCommentItem) {
            e.preventDefault();
            e.stopPropagation();
            handleCommentDropdownAction(editCommentItem || deleteCommentItem || reportCommentItem);
            return;
        }
        
    }
    
    // Handle comment ellipsis menu toggle
    function handleCommentEllipsisMenu(ellipsisButton) {
        const commentId = ellipsisButton.dataset.commentId;
        const dropdown = document.querySelector(`.dropdown-menu[data-comment-id="${commentId}"]`);
        
        if (dropdown) {
            // Close all other dropdowns first (both review and comment dropdowns)
            document.querySelectorAll('.dropdown-menu[data-review-id], .dropdown-menu[data-comment-id]').forEach(menu => {
                if (menu !== dropdown) {
                    menu.style.display = 'none';
                }
            });
            
            // Toggle current dropdown
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        }
    }
    
    // Handle comment dropdown menu actions
    function handleCommentDropdownAction(dropdownItem) {
        const action = dropdownItem.dataset.action;
        const commentId = dropdownItem.dataset.commentId;
        const reviewId = dropdownItem.dataset.reviewId;
        const locationId = dropdownItem.dataset.locationId;
        
        // Close the dropdown
        const dropdown = dropdownItem.closest('.dropdown-menu');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
        
        if (action === 'edit') {
            // Find the comment text element to make editable
            const commentElement = document.querySelector(`[data-comment-id="${commentId}"][data-editable="comment"]`);
            
            if (commentElement) {
                const originalContent = commentElement.getAttribute('data-original-content');
                const ids = {
                    locationId: locationId,
                    reviewId: reviewId,
                    commentId: commentId
                };
                
                // Use the editing system
                if (window.EditingSystem) {
                    window.EditingSystem.makeEditable(commentElement, 'comment', ids, originalContent);
                }
            }
        } else if (action === 'delete') {
            // Confirm deletion
            if (confirm('Are you sure you want to delete this comment?')) {
                deleteComment(commentId, reviewId, locationId);
            }
        } else if (action === 'report') {
            // Handle comment reporting - open report modal
            if (window.ReportModal) {
                window.ReportModal.openModal('comment', commentId, locationId, reviewId);
            }
        }
    }
    
    // Delete a comment
    function deleteComment(commentId, reviewId, locationId) {
        fetch(`/api/viewing-locations/${locationId}/reviews/${reviewId}/comments/${commentId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': config.csrfToken,
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete comment');
            }
            
            // Remove comment from DOM
            const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`).closest('.comment');
            if (commentElement) {
                commentElement.remove();
            }
            
            // Update comment count
            const reviewCard = document.querySelector(`[data-review-id="${reviewId}"]`).closest('.review-card');
            const countElement = reviewCard.querySelector('.comments-count');
            if (countElement) {
                const currentCount = parseInt(countElement.textContent);
                const newCount = Math.max(0, currentCount - 1);
                countElement.textContent = `${newCount} Comment${newCount !== 1 ? 's' : ''}`;
            }
        })
        .catch(error => {
            console.error('Error deleting comment:', error);
            alert('Failed to delete comment. Please try again.');
        });
    }
    
    
    // Handle outside clicks to close comment dropdowns
    function setupOutsideClickHandler() {
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.ellipsis-menu-wrapper')) {
                document.querySelectorAll('.dropdown-menu[data-comment-id]').forEach(menu => {
                    menu.style.display = 'none';
                });
            }
        });
    }
    
    // Create a new comment element
    function createCommentElement(comment) {
        const div = document.createElement('div');
        div.className = 'comment';

        // Handle both the old and new response formats
        const username = comment.user.username || comment.user;
        const profilePicUrl = comment.user.profile_picture_url || comment.user_profile_picture;
        
        // Check if this comment is from the current user
        const isCurrentUser = username === config.currentUsername;

        // Create vote controls based on user authentication and ownership
        const isCommentOwner = config.isAuthenticated && username === config.currentUsername;
        const upvoteCount = comment.upvote_count || 0;
        const downvoteCount = comment.downvote_count || 0;
        const userVote = comment.user_vote;
        
        // SVG icons as strings for JavaScript
        const thumbsUpIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-thumbs-up">
            <path d="M7 10v12"/>
            <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/>
        </svg>`;
        
        const thumbsDownIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-thumbs-down">
            <path d="M17 14V2"/>
            <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/>
        </svg>`;

        let voteControls = '';
        if (config.isAuthenticated && !isCommentOwner) {
            // Interactive voting buttons for authenticated users (not comment owner)
            voteControls = `
                    <button class="vote-button upvote ${userVote === 'up' ? 'voted' : ''}"
                            data-comment-id="${comment.id}"
                            data-review-id="${comment.review || comment.review_id}"
                            data-location-id="${comment.location || config.locationId}"
                            data-vote-type="up">
                        ${thumbsUpIcon}
                    </button>
                    <span class="upvote-count">${upvoteCount}</span>
                    
                    <button class="vote-button downvote ${userVote === 'down' ? 'voted' : ''}"
                            data-comment-id="${comment.id}"
                            data-review-id="${comment.review || comment.review_id}"
                            data-location-id="${comment.location || config.locationId}"
                            data-vote-type="down">
                        ${thumbsDownIcon}
                    </button>
                    <span class="downvote-count">${downvoteCount}</span>
            `;
        } else {
            // Disabled buttons for comment owners or non-authenticated users
            voteControls = `
                    <button class="vote-button disabled" disabled>
                        ${thumbsUpIcon}
                    </button>
                    <span class="upvote-count">${upvoteCount}</span>
                    
                    <button class="vote-button disabled" disabled>
                        ${thumbsDownIcon}
                    </button>
                    <span class="downvote-count">${downvoteCount}</span>
            `;
        }

        // Create ellipsis menu for authenticated users
        let ellipsisMenu = '';
        if (config.isAuthenticated) {
            const ellipsisIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-ellipsis">
                <circle cx="12" cy="12" r="1"/>
                <circle cx="19" cy="12" r="1"/>
                <circle cx="5" cy="12" r="1"/>
            </svg>`;
            
            const pencilIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pencil">
                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                <path d="m15 5 4 4"/>
            </svg>`;
            
            const trashIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash-2">
                <path d="M3 6h18"/>
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                <line x1="10" x2="10" y1="11" y2="17"/>
                <line x1="14" x2="14" y1="11" y2="17"/>
            </svg>`;
            
            const flagIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-flag">
                <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
                <line x1="4" x2="4" y1="22" y2="15"/>
            </svg>`;

            if (isCurrentUser) {
                // Owner options: Edit and Delete
                ellipsisMenu = `
                    <div class="ellipsis-menu-wrapper">
                        <button class="ellipsis-menu-button" data-comment-id="${comment.id}">
                            ${ellipsisIcon}
                        </button>
                        <div class="dropdown-menu" data-comment-id="${comment.id}" style="display: none;">
                            <button class="dropdown-item edit-comment-item" data-action="edit" data-comment-id="${comment.id}" data-review-id="${comment.review || comment.review_id}" data-location-id="${comment.location || config.locationId}">
                                ${pencilIcon}
                                <span>Edit</span>
                            </button>
                            <button class="dropdown-item delete-comment-item" data-action="delete" data-comment-id="${comment.id}" data-review-id="${comment.review || comment.review_id}" data-location-id="${comment.location || config.locationId}">
                                ${trashIcon}
                                <span>Delete</span>
                            </button>
                            ${config.isOwner && !isCurrentUser ? `
                                <button class="dropdown-item report-comment-item" data-action="report" data-comment-id="${comment.id}" data-review-id="${comment.review || comment.review_id}" data-location-id="${comment.location || config.locationId}">
                                    ${flagIcon}
                                    <span>Report</span>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                `;
            } else {
                // Non-owner options: Report only
                ellipsisMenu = `
                    <div class="ellipsis-menu-wrapper">
                        <button class="ellipsis-menu-button" data-comment-id="${comment.id}">
                            ${ellipsisIcon}
                        </button>
                        <div class="dropdown-menu" data-comment-id="${comment.id}" style="display: none;">
                            <button class="dropdown-item report-comment-item" data-action="report" data-comment-id="${comment.id}" data-review-id="${comment.review || comment.review_id}" data-location-id="${comment.location || config.locationId}">
                                ${flagIcon}
                                <span>Report</span>
                            </button>
                        </div>
                    </div>
                `;
            }
        }

        div.innerHTML = `
            <img src="${profilePicUrl}"
                 alt="${username}'s profile picture"
                 class="comment-profile-picture">
            <div class="comment-content">
                <div class="comment-header">
                    <span class="comment-username">${username}</span>
                    <span class="comment-date">${formatDate(comment.created_at)}</span>
                    ${comment.is_edited ? '<span class="edited-indicator">(edited)</span>' : ''}
                </div>
                <p class="comment-text"
                   data-editable="comment"
                   data-location-id="${comment.location || config.locationId}"
                   data-review-id="${comment.review || comment.review_id}"
                   data-comment-id="${comment.id}"
                   data-original-content="${comment.content}">
                    ${comment.content}
                </p>
                <div class="comment-vote-controls">
                    ${voteControls}
                    ${ellipsisMenu}
                </div>
            </div>
        `;
        return div;
    }

    // Format date for display
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }
    
    // Public API
    return {
        init: init,
        createCommentElement: createCommentElement
    };
})();

// Voting System Component
window.VotingSystem = (function() {
    'use strict';
    
    let config = {};
    let eventBus = null;
    
    // Initialize the voting system
    function init(pageConfig, bus) {
        config = pageConfig;
        eventBus = bus;
        
        setupEventListeners();
    }
    
    // Setup event listeners for voting
    function setupEventListeners() {
        // Use event delegation for vote buttons
        document.addEventListener('click', function(e) {
            const voteButton = e.target.closest('.vote-button');
            if (voteButton && !voteButton.disabled) {
                e.preventDefault();
                handleVote(voteButton);
            }
        });
    }
    
    // Handle vote button clicks
    function handleVote(button) {
        const voteType = button.dataset.voteType;
        const reviewId = button.dataset.reviewId;
        const commentId = button.dataset.commentId;
        const locationId = button.dataset.locationId;
        
        // Determine if this is a review vote or comment vote
        const isReviewVote = reviewId && !commentId;
        const isCommentVote = commentId && reviewId;
        
        if (!isReviewVote && !isCommentVote) {
            console.error('Invalid vote configuration');
            return;
        }
        
        // Construct API endpoint
        let apiUrl;
        if (isReviewVote) {
            apiUrl = `/api/viewing-locations/${locationId}/reviews/${reviewId}/vote/`;
        } else {
            apiUrl = `/api/viewing-locations/${locationId}/reviews/${reviewId}/comments/${commentId}/vote/`;
        }
        
        // Disable the button during the request
        button.disabled = true;
        
        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': config.csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ vote_type: voteType }),
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(error => {
                    throw new Error(error.detail || 'Failed to submit vote');
                });
            }
            return response.json();
        })
        .then(data => {
            // Update the vote counts and button states
            updateVoteDisplay(button, data, isReviewVote);
        })
        .catch(error => {
            console.error('Error submitting vote:', error);
            // Could show a user-friendly error message here
        })
        .finally(() => {
            // Re-enable the button
            button.disabled = false;
        });
    }
    
    // Update vote display after successful vote
    function updateVoteDisplay(clickedButton, data, isReviewVote) {
        const container = clickedButton.closest('.vote-controls, .comment-vote-controls');
        if (!container) return;

        // Get the vote count elements
        const upvoteCount = container.querySelector('.upvote-count');
        const downvoteCount = container.querySelector('.downvote-count');
        const upvoteButton = container.querySelector('.vote-button.upvote');
        const downvoteButton = container.querySelector('.vote-button.downvote');

        // Update vote counts
        if (upvoteCount) upvoteCount.textContent = data.upvotes;
        if (downvoteCount) downvoteCount.textContent = data.downvotes;
        
        // Update button states based on user's current vote
        if (upvoteButton) {
            upvoteButton.classList.toggle('voted', data.user_vote === 'up');
        }
        if (downvoteButton) {
            downvoteButton.classList.toggle('voted', data.user_vote === 'down');
        }
        
        // If this is a review vote, also update the review metrics
        if (isReviewVote && window.ReviewSystem) {
            // Recalculate rating distribution after vote changes
            setTimeout(() => {
                window.ReviewSystem.calculateRatingDistribution();
            }, 100);
        }
    }
    
    // Public API
    return {
        init: init
    };
})();

// Editing System Component
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
        
        // Create edit controls container - no wrapper needed for reviews in edit mode
        const editControls = document.createElement('div');
        editControls.className = 'edit-controls';
        
        // For reviews, try to clone the template form for consistent styling
        let formHTML = '';
        if (type === 'review') {
            const reviewFormTemplate = document.getElementById('reviewFormTemplate');
            if (reviewFormTemplate) {
                // Clone the template and extract only the form element
                const templateClone = reviewFormTemplate.cloneNode(true);
                const formElement = templateClone.querySelector('.review-form');
                
                if (formElement) {
                    
                    // Update IDs to avoid conflicts
                    formElement.querySelectorAll('[id]').forEach(el => {
                        const oldId = el.id;
                        if (oldId.startsWith('template-')) {
                            // For image upload elements, use the pattern ImageUploadSystem expects
                            if (oldId === 'template-add-image-btn') {
                                el.id = `edit-add-image-btn-${ids.reviewId}`;
                            } else if (oldId === 'template-review-images-input') {
                                el.id = `edit-review-images-input-${ids.reviewId}`;
                            } else if (oldId === 'template-image-preview-container') {
                                el.id = `edit-image-preview-container-${ids.reviewId}`;
                            } else {
                                // For other template elements (like star inputs)
                                el.id = oldId.replace('template-', `edit-${ids.reviewId}-`);
                            }
                        } else {
                            el.id = `edit-${ids.reviewId}-${oldId}`;
                        }
                    });
                    
                    // Update labels to match new IDs
                    formElement.querySelectorAll('label[for]').forEach(label => {
                        const oldFor = label.getAttribute('for');
                        if (oldFor.startsWith('template-')) {
                            // Match the same ID transformation logic used above
                            if (oldFor === 'template-add-image-btn') {
                                label.setAttribute('for', `edit-add-image-btn-${ids.reviewId}`);
                            } else if (oldFor === 'template-review-images-input') {
                                label.setAttribute('for', `edit-review-images-input-${ids.reviewId}`);
                            } else if (oldFor === 'template-image-preview-container') {
                                label.setAttribute('for', `edit-image-preview-container-${ids.reviewId}`);
                            } else {
                                label.setAttribute('for', oldFor.replace('template-', `edit-${ids.reviewId}-`));
                            }
                        } else {
                            label.setAttribute('for', `edit-${ids.reviewId}-${oldFor}`);
                        }
                    });
                    
                    // Update placeholders
                    const commentInput = formElement.querySelector('.comment-input');
                    if (commentInput) {
                        commentInput.setAttribute('data-placeholder', 'Edit your review...');
                        commentInput.setAttribute('data-name', 'content');
                    }
                    
                    // Update button classes and text
                    const cancelBtn = formElement.querySelector('.cancel-review');
                    if (cancelBtn) {
                        cancelBtn.className = 'cancel-edit';
                        cancelBtn.textContent = 'Cancel';
                    }
                    
                    // Update submit button
                    const submitBtn = formElement.querySelector('.submit-review');
                    if (submitBtn) {
                        submitBtn.className = 'save-edit';
                        submitBtn.textContent = 'Save Changes';
                    }
                    
                    // Add form attributes for editing
                    formElement.setAttribute('data-edit-type', type);
                    formElement.setAttribute('data-location-id', ids.locationId);
                    formElement.setAttribute('data-review-id', ids.reviewId);
                    if (ids.commentId) {
                        formElement.setAttribute('data-comment-id', ids.commentId);
                    }
                    
                    // Parse original content
                    const originalData = parseOriginalContent(originalContent, type);
                    
                    // Pre-populate form with original data
                    if (originalData.content) {
                        // Set the content in the comment input
                        if (commentInput) {
                            commentInput.textContent = originalData.content;
                        }
                    }
                    
                    // Note: Rating and event listeners will be set after DOM insertion to preserve state
                    
                    formHTML = formElement.outerHTML;
                }
            }
        } else {
            // For comments, create a simpler form
            const originalData = parseOriginalContent(originalContent, type);
            
            // Get clean text content for comments
            let cleanContent = originalData.content || '';
            
            // If the content looks like JSON, try to parse it and extract the actual content
            if (cleanContent.startsWith('{') && cleanContent.includes('"content"')) {
                try {
                    const parsed = JSON.parse(cleanContent);
                    cleanContent = parsed.content || cleanContent;
                } catch (e) {
                    // If parsing fails, use as-is
                }
            }
            
            formHTML = `
                <form class="edit-form" data-edit-type="${type}" data-location-id="${ids.locationId}" data-review-id="${ids.reviewId}" data-comment-id="${ids.commentId}">
                    <div class="comment-input editable" contenteditable="true" data-placeholder="Edit your comment..." data-name="content">
                        ${cleanContent}
                    </div>
                    <div class="comment-toolbar">
                        <div class="edit-actions">
                            <button type="button" class="cancel-edit">Cancel</button>
                            <button type="submit" class="save-edit">Save Changes</button>
                        </div>
                    </div>
                </form>
            `;
        }
        
        // Insert the edit form
        editControls.innerHTML = formHTML;
        element.parentNode.insertBefore(editControls, element.nextSibling);
        
        // Set the rating and event listeners for reviews AFTER DOM insertion to preserve state
        if (type === 'review') {
            const form = editControls.querySelector('.review-form');
            if (form) {
                // Set the rating
                const currentRating = element.getAttribute('data-rating');
                if (currentRating) {
                    const starInput = form.querySelector(`input[name="rating"][value="${currentRating}"]`);
                    if (starInput) {
                        starInput.checked = true;
                    }
                }
                
                // Add event listeners to the actual DOM elements
                addEditEventListeners(form, type, ids, element);
            }
        }
        
        // Add event listeners for the simple comment form
        if (type === 'comment') {
            const form = editControls.querySelector('.edit-form');
            if (form) {
                addEditEventListeners(form, type, ids, element);
            }
        }
        
        // Initialize image upload system for review editing
        if (type === 'review' && window.ImageUploadSystem) {
            // Get existing images for this review
            const reviewCard = element.closest('.review-card');
            const existingImages = reviewCard ? reviewCard.querySelectorAll('.review-photos .review-photo-thumbnail') : [];
            
            if (existingImages.length > 0) {
                const form = editControls.querySelector('.review-form');
                if (form) {
                    // Create preview elements for existing photos
                    const previewContainer = form.querySelector('.image-preview-container');
                    if (previewContainer) {
                        existingImages.forEach((img, index) => {
                            const previewDiv = document.createElement('div');
                            previewDiv.className = 'image-preview-item existing-photo';
                            previewDiv.innerHTML = `
                                <img src="${img.src}" alt="Existing photo ${index + 1}" class="preview-image">
                                <button type="button" class="remove-image-btn" data-existing-photo-id="${img.closest('.review-photo-item').getAttribute('data-photo-id')}" title="Remove existing image">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                </button>
                            `;
                            previewContainer.appendChild(previewDiv);
                        });
                    }
                    
                    // Update the upload UI with existing count
                    window.ImageUploadSystem.updateUploadUIWithExisting(form, existingImages.length);
                }
            }
        }
        
        // Initialize star rating for review editing
        if (type === 'review' && window.ReviewSystem) {
            const starContainer = editControls.querySelector('.star-rating');
            if (starContainer) {
                window.ReviewSystem.initializeStarRatingForContainer(starContainer);
                
                // Trigger visual update for already selected rating
                const checkedInput = starContainer.querySelector('input:checked');
                if (checkedInput) {
                    // Manually update the visual state since the change event was dispatched before listeners were attached
                    const labels = starContainer.querySelectorAll('label');
                    const inputs = starContainer.querySelectorAll('input');
                    const checkedIndex = Array.from(inputs).indexOf(checkedInput);
                    labels.forEach((label, index) => {
                        if (index <= checkedIndex) {
                            label.classList.add('filled');
                        } else {
                            label.classList.remove('filled');
                        }
                    });
                }
            }
        }
        
        // Focus the content input
        const contentInput = editControls.querySelector('.comment-input');
        if (contentInput) {
            setTimeout(() => {
                contentInput.focus();
                // Move cursor to end
                if (contentInput.contentEditable === 'true') {
                    const range = document.createRange();
                    const selection = window.getSelection();
                    range.selectNodeContents(contentInput);
                    range.collapse(false);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            }, 100);
        }
    }
    
    // Parse original content based on type
    function parseOriginalContent(originalContent, type) {
        if (type === 'review') {
            // For reviews, the original content includes rating and content
            // Try to parse as JSON first
            try {
                const parsed = JSON.parse(originalContent);
                return {
                    rating: parsed.rating,
                    content: parsed.content
                };
            } catch (e) {
                // If not JSON, treat as plain content
                return {
                    content: originalContent
                };
            }
        } else {
            // For comments, it's just the content
            return {
                content: originalContent
            };
        }
    }
    
    // Add event listeners for edit forms
    function addEditEventListeners(form, type, ids, originalElement) {
        // Handle form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            handleEditSubmit(this, type, ids, originalElement);
        });
        
        // Handle cancel button
        const cancelBtn = form.querySelector('.cancel-edit');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function(e) {
                e.preventDefault();
                cancelEdit(originalElement);
            });
        }
    }
    
    // Handle edit form submission
    function handleEditSubmit(form, type, ids, originalElement) {
        const formData = new FormData(form);
        const contentInput = form.querySelector('.comment-input');

        // Get plain text content from contenteditable div or input
        let content = '';

        if (contentInput) {
            if (contentInput.contentEditable === 'true') {
                content = contentInput.textContent.trim();
            } else {
                content = contentInput.value ? contentInput.value.trim() : '';
            }
        }
        
        
        // For comments, content is required, but reviews can be empty (just rating/photos)
        if (type === 'comment' && !content) {
            alert('Please enter some content for your comment.');
            return;
        }
        
        // Use FormData to include photo deletions and other form data
        formData.set('content', content);
        
        // For reviews, ensure rating and location are in FormData
        if (type === 'review') {
            const ratingInput = form.querySelector('input[name="rating"]:checked');
            if (ratingInput) {
                formData.set('rating', ratingInput.value);
            }
            
            // Add the location ID (required by serializer)
            formData.set('location', ids.locationId);
            
            // Collect photo IDs marked for deletion
            const photosToDelete = [];
            const markedItems = form.querySelectorAll('.image-preview-item.marked-for-deletion[data-photo-to-delete]');
            markedItems.forEach(item => {
                const photoId = item.getAttribute('data-photo-to-delete');
                if (photoId) {
                    photosToDelete.push(parseInt(photoId, 10));
                }
            });
            
            // Send photo deletion data in the format the backend expects
            if (photosToDelete.length > 0) {
                formData.set('delete_photo_ids', JSON.stringify(photosToDelete));
            } else {
            }
        }
        
        // Determine API endpoint
        let apiUrl;
        if (type === 'review') {
            apiUrl = `/api/viewing-locations/${ids.locationId}/reviews/${ids.reviewId}/`;
        } else {
            apiUrl = `/api/viewing-locations/${ids.locationId}/reviews/${ids.reviewId}/comments/${ids.commentId}/`;
        }
        
        
        // Disable form during submission
        const submitBtn = form.querySelector('.save-edit');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';
        
        // Submit the edit using FormData
        fetch(apiUrl, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': config.csrfToken,
                // Remove Content-Type header - let browser set it for FormData
            },
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('Server response status:', response.status);
                    console.error('Server response text:', text);
                    try {
                        const error = JSON.parse(text);
                        console.error('Parsed error:', error);
                        throw new Error(error.detail || JSON.stringify(error) || 'Failed to save changes');
                    } catch (e) {
                        throw new Error(`Server error ${response.status}: ${text}`);
                    }
                });
            }
            return response.json();
        })
        .then(data => {
            
            // WORKAROUND: Server might return stale data due to timing issues
            // Use the content we know was sent since backend is confirmed saving correctly
            if (type === 'review') {
                const sentContent = formData.get('content');
                if (sentContent) {
                    data.comment = sentContent;
                }

                // Also ensure rating is updated with what was sent
                const sentRating = formData.get('rating');
                if (sentRating) {
                    data.rating = parseInt(sentRating, 10);
                }
            }
            
            // Update the original element with new content
            updateOriginalElement(originalElement, data, type);
            
            // Remove edit mode
            cancelEdit(originalElement);
            
            // Update metrics if this was a review
            if (type === 'review' && window.ReviewSystem) {
                setTimeout(() => {
                    window.ReviewSystem.calculateRatingDistribution();
                }, 100);
            }
        })
        .catch(error => {
            console.error('Error saving changes:', error);
            alert('Failed to save changes. Please try again.');
        })
        .finally(() => {
            // Re-enable form
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    }
    
    // Update original element with edited content
    function updateOriginalElement(element, data, type) {
        if (type === 'review') {
            // Update review content
            const newContent = data.comment || data.content || '';
            element.textContent = newContent;
            
            // Update data-rating attribute
            if (data.rating) {
                element.setAttribute('data-rating', data.rating);
            }
            
            // Update data-original-content attribute
            element.setAttribute('data-original-content', data.comment || data.content || '');
            
            // Update rating display
            const reviewCard = element.closest('.review-card');
            if (reviewCard && data.rating) {
                const ratingDisplay = reviewCard.querySelector('.rating-display');
                if (ratingDisplay) {
                    // Clear existing stars
                    ratingDisplay.innerHTML = '';
                    
                    // Create new stars based on the rating
                    for (let i = 1; i <= 5; i++) {
                        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                        svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
                        svg.setAttribute('width', '16');
                        svg.setAttribute('height', '16');
                        svg.setAttribute('viewBox', '0 0 24 24');
                        svg.setAttribute('stroke', 'currentColor');
                        svg.setAttribute('stroke-width', '2');
                        svg.setAttribute('stroke-linecap', 'round');
                        svg.setAttribute('stroke-linejoin', 'round');
                        
                        if (i <= data.rating) {
                            // Filled star
                            svg.setAttribute('fill', 'currentColor');
                            svg.setAttribute('class', 'lucide lucide-star filled');
                            svg.style.color = 'var(--golden)';
                            svg.style.fill = 'var(--golden)';
                        } else {
                            // Empty star
                            svg.setAttribute('fill', 'none');
                            svg.setAttribute('class', 'lucide lucide-star');
                            svg.style.color = 'var(--text-tertiary)';
                        }
                        
                        // Add the path element
                        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                        path.setAttribute('d', 'M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.123 2.123 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.123 2.123 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.122 2.122 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.122 2.122 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.122 2.122 0 0 0 1.597-1.16z');
                        
                        svg.appendChild(path);
                        ratingDisplay.appendChild(svg);
                    }
                }
            }
            
            // Update photos display if photos data is included in response
            if (reviewCard && data.photos !== undefined) {
                const photosSection = reviewCard.querySelector('.review-photos');
                if (data.photos && data.photos.length > 0) {
                    // Create new photos HTML
                    let photosHTML = '<div class="review-photos" data-image-count="' + data.photos.length + '">';
                    data.photos.forEach((photo, index) => {
                        photosHTML += `
                            <div class="review-photo-item" data-photo-id="${photo.id}">
                                <img src="${photo.thumbnail_url}" 
                                     alt="Review photo ${index + 1}"
                                     class="review-photo-thumbnail"
                                     data-full-url="${photo.image_url}"
                                     data-author="${data.user}"
                                     data-author-avatar="${data.user_avatar || ''}"
                                     data-review-date="${new Date().toLocaleDateString()}"
                                     data-location-name="${data.location_name || ''}"
                                     data-location-address="${data.location_address || ''}"
                                     loading="lazy">
                                ${photo.caption ? `<span class="photo-caption">${photo.caption}</span>` : ''}
                            </div>
                        `;
                    });
                    photosHTML += '</div>';
                    
                    // Replace existing photos section
                    if (photosSection) {
                        photosSection.outerHTML = photosHTML;
                    } else {
                        // Insert photos after review comment
                        element.insertAdjacentHTML('afterend', photosHTML);
                    }
                } else {
                    // No photos left, remove photos section
                    if (photosSection) {
                        photosSection.remove();
                    }
                }
            }
            
            // Add edited indicator
            const reviewHeader = reviewCard ? reviewCard.querySelector('.review-header') : null;
            if (reviewHeader) {
                let editedIndicator = reviewHeader.querySelector('.edited-indicator');
                if (!editedIndicator) {
                    editedIndicator = document.createElement('span');
                    editedIndicator.className = 'edited-indicator';
                    editedIndicator.textContent = '(edited)';
                    reviewHeader.appendChild(editedIndicator);
                }
            }
        } else {
            // Update comment content
            element.textContent = data.content;
            
            // Add edited indicator
            const commentHeader = element.closest('.comment').querySelector('.comment-header');
            if (commentHeader) {
                let editedIndicator = commentHeader.querySelector('.edited-indicator');
                if (!editedIndicator) {
                    editedIndicator = document.createElement('span');
                    editedIndicator.className = 'edited-indicator';
                    editedIndicator.textContent = '(edited)';
                    commentHeader.appendChild(editedIndicator);
                }
            }
        }
        
        // Update the original content attribute with the JSON format expected by parseOriginalContent
        element.setAttribute('data-original-content', JSON.stringify({
            content: data.comment || data.content || '',
            rating: data.rating
        }));
    }
    
    // Cancel edit mode
    function cancelEdit(element) {
        // Remove edit-mode class
        element.classList.remove('edit-mode');
        
        // Remove edit controls - they are inserted as the next sibling
        const editControls = element.nextElementSibling;
        if (editControls && editControls.classList.contains('edit-controls')) {
            editControls.remove();
        }
        
        // Show original photos if they were hidden
        const hiddenPhotos = element.closest('.review-card')?.querySelector('[data-hidden-for-edit="true"]');
        if (hiddenPhotos) {
            hiddenPhotos.style.display = '';
            hiddenPhotos.removeAttribute('data-hidden-for-edit');
        }
    }
    
    // Decode HTML entities
    function decodeHTMLEntities(text) {
        const textArea = document.createElement('textarea');
        textArea.innerHTML = text;
        return textArea.value;
    }

    // Public API
    return {
        init: init,
        makeEditable: makeEditable
    };
})();

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
                const form = removeBtn.closest('form');
                
                // Check if this is an existing photo or a new upload
                if (removeBtn.hasAttribute('data-existing-photo-id')) {
                    // Handle existing photo removal
                    const photoId = removeBtn.dataset.existingPhotoId;
                    const previewItem = removeBtn.closest('.image-preview-item');
                    
                    // Hide the preview and mark for deletion
                    previewItem.style.display = 'none';
                    previewItem.classList.add('marked-for-deletion');
                    
                    // Add photo ID to deletion list (we'll collect all IDs before form submission)
                    previewItem.setAttribute('data-photo-to-delete', photoId);
                    
                    // Update the existing count
                    const currentExisting = getFormExistingCount(form);
                    setFormExistingCount(form, currentExisting - 1);
                    
                    // Update UI
                    const files = getFormFiles(form);
                    updateUploadUI(form, files);
                } else {
                    // Handle new upload removal
                    const index = parseInt(removeBtn.dataset.index);
                    removeImage(index, form);
                }
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

// Report Modal Component
window.ReportModal = (function() {
    'use strict';
    
    let config = {};
    let currentReportTarget = null;
    let selectedCategory = null;
    
    // Initialize the report modal system
    function init(pageConfig) {
        config = pageConfig;
        
        // Wait for DOM to be ready if it's not already
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupEventListeners);
        } else {
            setupEventListeners();
        }
    }
    
    // Setup event listeners for modal interactions
    function setupEventListeners() {
        const modal = document.getElementById('contentReportModal');
        if (!modal) {
            console.error('Report modal element not found!');
            return;
        }
        const closeButton = modal.querySelector('.report-modal-close');
        const cancelButton = modal.querySelector('.report-modal-button.cancel');
        const submitButton = modal.querySelector('.report-modal-button.submit');
        const categoryButtons = modal.querySelectorAll('.report-category');
        const descriptionSection = document.getElementById('reportDescriptionSection');
        
        // Close modal events
        closeButton.addEventListener('click', closeModal);
        cancelButton.addEventListener('click', closeModal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // ESC key to close modal
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                closeModal();
            }
        });
        
        // Category selection
        categoryButtons.forEach(button => {
            button.addEventListener('click', function() {
                selectCategory(this);
            });
        });
        
        // Submit report
        submitButton.addEventListener('click', submitReport);
    }
    
    // Open the report modal
    function openModal(targetType, targetId, locationId, reviewId = null) {
        currentReportTarget = {
            type: targetType, // 'review' or 'comment'
            id: targetId,
            locationId: locationId,
            reviewId: reviewId
        };
        
        // Update modal title based on target type
        const modalTitle = document.querySelector('.report-modal-title');
        modalTitle.textContent = targetType === 'review' ? 'Report Review' : 'Report Comment';
        
        // Reset modal state
        resetModal();
        
        // Show modal
        const modal = document.getElementById('contentReportModal');
        modal.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
    
    // Close the report modal
    function closeModal() {
        const modal = document.getElementById('contentReportModal');
        modal.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
        resetModal();
    }
    
    // Reset modal to initial state
    function resetModal() {
        selectedCategory = null;
        
        // Clear category selections
        const categoryButtons = document.querySelectorAll('.report-category');
        categoryButtons.forEach(button => {
            button.classList.remove('selected');
        });
        
        // Hide description section
        const descriptionSection = document.getElementById('reportDescriptionSection');
        descriptionSection.classList.remove('active');
        
        // Clear description
        const descriptionInput = document.getElementById('reportDescription');
        descriptionInput.value = '';
        
        // Disable submit button
        const submitButton = document.querySelector('.report-modal-button.submit');
        submitButton.disabled = true;
    }
    
    // Select a report category
    function selectCategory(categoryButton) {
        // Remove previous selection
        const categoryButtons = document.querySelectorAll('.report-category');
        categoryButtons.forEach(button => {
            button.classList.remove('selected');
        });
        
        // Select current category
        categoryButton.classList.add('selected');
        selectedCategory = categoryButton.dataset.reportType;
        
        // Show description section
        const descriptionSection = document.getElementById('reportDescriptionSection');
        descriptionSection.classList.add('active');
        
        // Enable submit button
        const submitButton = document.querySelector('.report-modal-button.submit');
        submitButton.disabled = false;
    }
    
    // Submit the report
    function submitReport() {
        if (!selectedCategory || !currentReportTarget) {
            return;
        }
        
        const submitButton = document.querySelector('.report-modal-button.submit');
        const originalText = submitButton.textContent;
        
        // Show loading state
        submitButton.disabled = true;
        submitButton.textContent = 'Submitting...';
        
        // Get description
        const description = document.getElementById('reportDescription').value.trim();
        
        // Prepare request data
        const reportData = {
            report_type: selectedCategory,
            description: description
        };
        
        // Determine API endpoint
        let apiUrl;
        if (currentReportTarget.type === 'review') {
            apiUrl = `/api/viewing-locations/${currentReportTarget.locationId}/reviews/${currentReportTarget.id}/report/`;
        } else {
            apiUrl = `/api/viewing-locations/${currentReportTarget.locationId}/reviews/${currentReportTarget.reviewId}/comments/${currentReportTarget.id}/report/`;
        }
        
        // Submit report
        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': config.csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(reportData),
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(error => {
                    throw new Error(error.detail || 'Failed to submit report');
                });
            }
            return response.json();
        })
        .then(data => {
            // Success
            closeModal();
            showSuccessNotification();
        })
        .catch(error => {
            console.error('Error submitting report:', error);
            showErrorNotification(error.message);
        })
        .finally(() => {
            // Restore button state
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        });
    }
    
    // Show success notification
    function showSuccessNotification() {
        // Create a modern toast notification instead of alert
        const notification = createNotification(
            'Report submitted successfully. Thank you for helping keep our community safe.',
            'success'
        );
        document.body.appendChild(notification);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 4000);
    }
    
    // Show error notification
    function showErrorNotification(message) {
        const notification = createNotification(
            message || 'Failed to submit report. Please try again.',
            'error'
        );
        document.body.appendChild(notification);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 4000);
    }
    
    // Create notification element
    function createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `report-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    ${type === 'success' ? 
                        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20,6 9,17 4,12"></polyline></svg>' :
                        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
                    }
                </div>
                <span class="notification-message">${message}</span>
            </div>
        `;
        
        // Add notification styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : '#ef4444'};
            color: white;
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            max-width: 400px;
            animation: slideIn 0.3s ease;
        `;
        
        // Add CSS for animation
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                .report-notification .notification-content {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .report-notification .notification-icon {
                    flex-shrink: 0;
                }
                .report-notification .notification-message {
                    flex: 1;
                    font-weight: 500;
                }
            `;
            document.head.appendChild(style);
        }
        
        return notification;
    }
    
    // Public API
    return {
        init: init,
        openModal: openModal,
        closeModal: closeModal
    };
})();