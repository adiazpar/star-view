// Initialize carousel and photo functionality after DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Get Django template variables from global config
    const config = window.locationDetailsConfig;
    const locationId = config.locationId;
    const isAuthenticated = config.isAuthenticated;
    const isOwner = config.isOwner;
    const currentUsername = config.currentUsername;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const mapboxToken = config.mapboxToken;
    const locationLongitude = config.locationLongitude;
    const locationLatitude = config.locationLatitude;
    const locationName = config.locationName;
    
    // Initialize Photo Gallery and Carousel
    loadPhotosAndInitialize();
    
    // Initialize review form if user can write a review
    if (isAuthenticated && !config.userHasReviewed && !isOwner) {
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
            }
        }
    }
    
    // Initialize star rating on existing form
    initializeStarRating();
    
    // Initialize review form toggle
    initializeReviewFormToggle();
    
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
            csrfInput.value = csrfToken;
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
        
        return formContent;
    }

    async function loadPhotosAndInitialize() {
        try {
            const response = await fetch(`/api/v1/viewing-locations/${locationId}/photos/`, {
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                const data = await response.json();
                const photos = data.results || data;
                
                initializeHeroCarousel(photos);
                initializePhotosGrid(photos);
                
                if (isAuthenticated) {
                    initializeUploadModal();
                }
            }
        } catch (error) {
            console.error('Error loading photos:', error);
            initializeHeroCarousel([]);
            initializePhotosGrid([]);
        }
    }

    function initializeHeroCarousel(photos) {
        const carouselContent = document.getElementById('carouselContent');
        const photoCredit = document.getElementById('photoCredit');
        const prevBtn = document.getElementById('carouselPrev');
        const nextBtn = document.getElementById('carouselNext');
        
        if (!photos || photos.length === 0) {
            // Show default map view
            carouselContent.innerHTML = `
                <div class="carousel-slide active">
                    <img src="https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v11/static/${locationLongitude},${locationLatitude},13/1200x500@2x?access_token=${mapboxToken}"
                         alt="Map view of ${locationName}">
                </div>
            `;
            photoCredit.innerHTML = 'Map data © Mapbox';
            prevBtn.style.display = 'none';
            nextBtn.style.display = 'none';
            return;
        }

        let currentSlide = 0;
        
        // Create slides
        carouselContent.innerHTML = photos.map((photo, index) => `
            <div class="carousel-slide ${index === 0 ? 'active' : ''}">
                <img src="${photo.image_url}" alt="${photo.caption || 'Location photo'}">
            </div>
        `).join('');
        
        function updatePhotoCredit() {
            const currentPhoto = photos[currentSlide];
            if (currentPhoto) {
                photoCredit.innerHTML = `Photo by ${currentPhoto.uploaded_by_username || 'Unknown'} • ${formatDate(currentPhoto.uploaded_at || currentPhoto.created_at)}`;
            }
        }
        
        function showSlide(index) {
            const slides = carouselContent.querySelectorAll('.carousel-slide');
            slides.forEach((slide, i) => {
                slide.classList.toggle('active', i === index);
            });
            currentSlide = index;
            updatePhotoCredit();
        }
        
        prevBtn.addEventListener('click', () => {
            const newIndex = currentSlide > 0 ? currentSlide - 1 : photos.length - 1;
            showSlide(newIndex);
        });
        
        nextBtn.addEventListener('click', () => {
            const newIndex = currentSlide < photos.length - 1 ? currentSlide + 1 : 0;
            showSlide(newIndex);
        });
        
        updatePhotoCredit();
        
        // Auto-advance carousel
        setInterval(() => {
            const newIndex = currentSlide < photos.length - 1 ? currentSlide + 1 : 0;
            showSlide(newIndex);
        }, 5000);
    }
    
    function initializePhotosGrid(photos) {
        const photosGrid = document.getElementById('photosGrid');
        const photosTitle = document.getElementById('photosTitle');
        
        photosTitle.textContent = `Photos (${photos.length})`;
        
        if (!photos || photos.length === 0) {
            photosGrid.innerHTML = `
                <div class="no-photos" style="grid-column: 1 / -1; text-align: center; padding: var(--space-xl); color: var(--text-tertiary);">
                    <i class="fas fa-image" style="font-size: 3rem; margin-bottom: var(--space-md); opacity: 0.5;"></i>
                    <p>No photos yet</p>
                    ${isAuthenticated ? '<p class="text-muted">Be the first to add a photo!</p>' : ''}
                </div>
            `;
            return;
        }
        
        photosGrid.innerHTML = photos.map(photo => `
            <div class="photo-thumbnail ${photo.is_primary ? 'primary' : ''}" data-photo-id="${photo.id}" onclick="openPhotoLightbox('${photo.image_url}')">
                <img src="${photo.thumbnail_url || photo.image_url}" alt="${photo.caption || 'Location photo'}" loading="lazy">
            </div>
        `).join('');
    }
    
    function initializeUploadModal() {
        const uploadBtn = document.getElementById('openUploadModal');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => {
                // Create and show upload modal
                const modal = createUploadModal();
                document.body.appendChild(modal);
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            });
        }
    }
    
    function createUploadModal() {
        const modal = document.createElement('div');
        modal.className = 'photo-upload-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Upload Photo</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <form class="photo-upload-form">
                    <div class="form-group">
                        <label for="photoFile">Select Photo</label>
                        <input type="file" id="photoFile" name="image" accept="image/*" required>
                        <div class="file-preview"></div>
                    </div>
                    <div class="form-group">
                        <label for="photoCaption">Caption (optional)</label>
                        <textarea id="photoCaption" name="caption" rows="3" placeholder="Describe this photo..."></textarea>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn-cancel">Cancel</button>
                        <button type="submit" class="btn-primary">
                            <i class="fas fa-upload"></i> Upload Photo
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        // Add event listeners
        const closeBtn = modal.querySelector('.modal-close');
        const cancelBtn = modal.querySelector('.btn-cancel');
        const form = modal.querySelector('.photo-upload-form');
        const fileInput = modal.querySelector('#photoFile');
        
        function closeModal() {
            modal.remove();
            document.body.style.overflow = '';
        }
        
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            const preview = modal.querySelector('.file-preview');
            
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 100%; height: auto; border-radius: var(--radius-sm);">`;
                };
                reader.readAsDataURL(file);
            }
        });
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const submitBtn = form.querySelector('.btn-primary');
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
            
            try {
                const response = await fetch(`/api/v1/viewing-locations/${locationId}/upload_photo/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData,
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    closeModal();
                    // Reload photos
                    loadPhotosAndInitialize();
                    showMessage('Photo uploaded successfully!', 'success');
                } else {
                    const error = await response.json();
                    throw new Error(error.detail || 'Upload failed');
                }
            } catch (error) {
                console.error('Upload error:', error);
                showMessage(error.message || 'Failed to upload photo', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Photo';
            }
        });
        
        return modal;
    }
    
    // Global functions
    window.openPhotoLightbox = function(imageSrc) {
        const lightbox = document.createElement('div');
        lightbox.className = 'photo-lightbox';
        lightbox.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.95); z-index: 2000; display: flex;
            align-items: center; justify-content: center; padding: var(--space-lg);
        `;
        lightbox.innerHTML = `
            <div style="position: relative; max-width: 90%; max-height: 90vh;">
                <img src="${imageSrc}" style="max-width: 100%; max-height: 90vh; object-fit: contain;">
                <button style="position: absolute; top: -40px; right: 0; background: none; border: none; color: white; font-size: 2rem; cursor: pointer;">&times;</button>
            </div>
        `;
        
        document.body.appendChild(lightbox);
        document.body.style.overflow = 'hidden';
        
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox || e.target.tagName === 'BUTTON') {
                lightbox.remove();
                document.body.style.overflow = '';
            }
        });
    };
    
    function showMessage(message, type) {
        const messageEl = document.createElement('div');
        messageEl.className = `gallery-message ${type}`;
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm);
            color: white; font-size: var(--font-size-sm); max-width: 300px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            background: ${type === 'success' ? 'var(--success)' : 'var(--negate)'};
        `;
        
        document.body.appendChild(messageEl);
        
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }
    
    function formatDate(dateString) {
        if (!dateString) return 'Unknown date';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return 'Invalid date';
        }
    }

    // Favorite functionality
    let isFavorited = false;

    function updateFavoriteButton() {
        const favoriteButton = document.querySelector('.favorite-button');
        const favoriteText = document.getElementById('favoriteText');

        if (favoriteButton && favoriteText) {
            favoriteButton.classList.toggle('favorited', isFavorited);
            favoriteText.textContent = isFavorited ? 'Remove from Favorites' : 'Add to Favorites';
        }
    }

    // Check initial favorite status when page loads
    if (isAuthenticated) {
        const favoriteButton = document.querySelector('.favorite-button');
        if (favoriteButton) {
            fetch(`/api/v1/viewing-locations/${locationId}/favorite/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                isFavorited = data.is_favorited;
                updateFavoriteButton();
            })
            .catch(error => console.error('Error checking favorite status:', error));

            // Add click handler for favorite button
            favoriteButton.addEventListener('click', function() {
                const endpoint = isFavorited ? 'unfavorite' : 'favorite';

                fetch(`/api/v1/viewing-locations/${locationId}/${endpoint}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    isFavorited = !isFavorited;
                    updateFavoriteButton();
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                });
            });
        }
    }
    // Add delete review functionality
    const reviewsList = document.querySelector('.reviews-list');
    if (reviewsList) {
        reviewsList.addEventListener('click', function(e) {
            // Ellipsis menu button handling
            const ellipsisButton = e.target.closest('.ellipsis-menu-button');
            if (ellipsisButton) {
                e.preventDefault();
                e.stopPropagation();
                
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
            
            // Comment edit button handling
            const commentEditBtn = e.target.closest('.comment-edit-btn');
            if (commentEditBtn) {
                e.preventDefault();
                e.stopPropagation();
                
                const commentId = commentEditBtn.dataset.commentId;
                const reviewId = commentEditBtn.dataset.reviewId;
                const locationIdVal = commentEditBtn.dataset.locationId;
                
                // Find the comment text element to make editable
                const commentElement = document.querySelector(`[data-comment-id="${commentId}"][data-editable="comment"]`);
                
                if (commentElement) {
                    const originalContent = commentElement.getAttribute('data-original-content');
                    const ids = {
                        locationId: locationIdVal,
                        reviewId: reviewId,
                        commentId: commentId
                    };
                    
                    makeEditable(commentElement, 'comment', ids, originalContent);
                }
                
                return;
            }
            
            // Edit item in dropdown handling
            const editItem = e.target.closest('.edit-item');
            if (editItem) {
                e.preventDefault();
                e.stopPropagation();
                
                const reviewId = editItem.dataset.reviewId;
                // locationId is already available in scope
                
                // Find the review comment element to make editable
                const reviewElement = document.querySelector(`[data-review-id="${reviewId}"][data-editable="review"]`);
                
                if (reviewElement) {
                    const originalContent = reviewElement.getAttribute('data-original-content');
                    const ids = {
                        locationId: locationId,
                        reviewId: reviewId
                    };
                    
                    makeEditable(reviewElement, 'review', ids, originalContent);
                    
                    // Close the dropdown menu
                    const dropdown = editItem.closest('.dropdown-menu');
                    if (dropdown) {
                        dropdown.style.display = 'none';
                    }
                }
                
                return;
            }
            
            // Delete item in dropdown handling
            const deleteItem = e.target.closest('.delete-item');
            if (deleteItem) {
                e.preventDefault();
                e.stopPropagation();
                
                const reviewId = deleteItem.dataset.reviewId;
                
                if (confirm('Are you sure you want to delete your review?')) {
                    fetch(`/delete-review/${reviewId}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
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
                            // Close the dropdown menu
                            const dropdown = deleteItem.closest('.dropdown-menu');
                            if (dropdown) {
                                dropdown.style.display = 'none';
                            }
                            
                            // Remove the review card
                            deleteItem.closest('.review-card').remove();

                            // Check if there are any reviews left
                            if (!document.querySelector('.review-card')) {
                                reviewsList.innerHTML = '<div class="no-reviews">No reviews yet</div>';
                            }

                            // Update the toggle button state if it exists
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
                                    // Create the square-pen icon SVG
                                    const newIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-square-pen">
                                        <path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                        <path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/>
                                    </svg>`;
                                    currentIcon.outerHTML = newIcon;
                                }
                            }

                            // Update the existing review form container
                            const existingFormContainer = document.getElementById('reviewFormContainer');
                            if (existingFormContainer && data.should_show_form) {
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
                                }, 100);
                            }
                            
                            // Recalculate and update the metrics card
                            setTimeout(() => calculateRatingDistribution(), 100);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Failed to delete review. Please try again.');
                    });
                }
            }

            // Vote button handling:
            const voteButton = e.target.closest('.vote-button');
            if (voteButton && !voteButton.classList.contains('disabled')) {
                e.preventDefault();

                const reviewId = voteButton.dataset.reviewId;
                const commentId = voteButton.dataset.commentId;
                const locationId = voteButton.dataset.locationId;
                const voteType = voteButton.dataset.voteType;
                
                // Determine if this is a review vote or comment vote
                const isCommentVote = !!commentId;
                const voteContainer = voteButton.closest(isCommentVote ? '.comment-vote-controls' : '.vote-controls');
                
                // Build the appropriate API endpoint
                let endpoint;
                if (isCommentVote) {
                    endpoint = `/api/v1/viewing-locations/${locationId}/reviews/${reviewId}/comments/${commentId}/vote/`;
                } else {
                    endpoint = `/api/v1/viewing-locations/${locationId}/reviews/${reviewId}/vote/`;
                }

                fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ vote_type: voteType }),
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    // Update vote counts
                    const upvoteCountElement = voteContainer.querySelector('.upvote-count');
                    const downvoteCountElement = voteContainer.querySelector('.downvote-count');
                    
                    if (upvoteCountElement) {
                        upvoteCountElement.textContent = data.upvotes;
                    }
                    if (downvoteCountElement) {
                        downvoteCountElement.textContent = data.downvotes;
                    }

                    // Update button states
                    const upvoteButton = voteContainer.querySelector('.upvote');
                    const downvoteButton = voteContainer.querySelector('.downvote');

                    // Update visual state
                    upvoteButton.classList.remove('voted');
                    downvoteButton.classList.remove('voted');

                    if (data.user_vote === 'up') {
                        upvoteButton.classList.add('voted');
                    } else if (data.user_vote === 'down') {
                        downvoteButton.classList.add('voted');
                    }

                    // Update data attributes
                    upvoteButton.dataset.currentVote = data.user_vote || '';
                    downvoteButton.dataset.currentVote = data.user_vote || '';
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to register vote. Please try again.');
                });
            }
        });
    }

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
    
    // Call this after DOM is loaded
    setTimeout(calculateRatingDistribution, 100);
    // Handle comment section toggling
    document.querySelectorAll('.comments-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const reviewId = this.dataset.reviewId;
            const commentsContainer = document.getElementById(`comments-${reviewId}`);
            const isHidden = commentsContainer.style.display === 'none';

            commentsContainer.style.display = isHidden ? 'block' : 'none';
        });
    });

    // Initialize formatting functionality for comment forms
    initializeCommentFormatting();

    // Handle comment submission
    document.querySelectorAll('.comment-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const reviewId = this.dataset.reviewId;
            const locationId = this.dataset.locationId;
            const commentInput = this.querySelector('.comment-input');
            const hiddenInput = this.querySelector('.hidden-content');
            
            // Get content from hidden input (markdown) or contenteditable div
            let content;
            if (hiddenInput && hiddenInput.value.trim()) {
                content = hiddenInput.value.trim();
            } else if (commentInput.contentEditable === 'true') {
                content = htmlToMarkdown(commentInput.innerHTML).trim();
            } else {
                content = commentInput.value.trim();
            }
            if (!content) return;

            fetch(`/api/v1/viewing-locations/${locationId}/reviews/${reviewId}/comments/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
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
                    commentInput.innerHTML = '';
                    hiddenInput.value = '';
                    
                    // Clear all formatting button states
                    const form = commentInput.closest('.comment-form');
                    const buttons = form.querySelectorAll('.formatting-btn');
                    buttons.forEach(button => button.classList.remove('active'));
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
        });
    });

    function createCommentElement(comment) {
        const div = document.createElement('div');
        div.className = 'comment';

        // Handle both the old and new response formats
        const username = comment.user.username || comment.user;
        const profilePicUrl = comment.user.profile_picture_url || comment.user_profile_picture;
        
        // Check if this comment is from the current user
        const isCurrentUser = username === currentUsername;
        const editButton = isCurrentUser ? `
            <button class="comment-edit-btn" 
                    data-comment-id="${comment.id}"
                    data-review-id="${comment.review || comment.review_id}"
                    data-location-id="${comment.location || locationId}"
                    title="Edit comment">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pencil">
                    <path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/>
                    <path d="m15 5 4 4"/>
                </svg>
            </button>
        ` : '';

        // Create vote controls based on user authentication and ownership
        const isCommentOwner = isAuthenticated && username === currentUsername;
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
        if (isAuthenticated && !isCommentOwner) {
            // Interactive voting buttons for authenticated users (not comment owner)
            voteControls = `
                <div class="comment-vote-controls">
                    <button class="vote-button upvote ${userVote === 'up' ? 'voted' : ''}"
                            data-comment-id="${comment.id}"
                            data-review-id="${comment.review || comment.review_id}"
                            data-location-id="${comment.location || locationId}"
                            data-vote-type="up">
                        ${thumbsUpIcon}
                    </button>
                    <span class="upvote-count">${upvoteCount}</span>
                    
                    <button class="vote-button downvote ${userVote === 'down' ? 'voted' : ''}"
                            data-comment-id="${comment.id}"
                            data-review-id="${comment.review || comment.review_id}"
                            data-location-id="${comment.location || locationId}"
                            data-vote-type="down">
                        ${thumbsDownIcon}
                    </button>
                    <span class="downvote-count">${downvoteCount}</span>
                </div>
            `;
        } else {
            // Disabled buttons for comment owners or non-authenticated users
            voteControls = `
                <div class="comment-vote-controls">
                    <button class="vote-button disabled" disabled>
                        ${thumbsUpIcon}
                    </button>
                    <span class="upvote-count">${upvoteCount}</span>
                    
                    <button class="vote-button disabled" disabled>
                        ${thumbsDownIcon}
                    </button>
                    <span class="downvote-count">${downvoteCount}</span>
                </div>
            `;
        }

        div.innerHTML = `
            <img src="${profilePicUrl}"
                 alt="${username}'s profile picture"
                 class="comment-profile-picture">
            <div class="comment-content">
                <div class="comment-header">
                    <span class="comment-username">${username}</span>
                    <span class="comment-date">${formatDate(comment.created_at)}</span>
                    ${editButton}
                </div>
                <p class="comment-text" 
                   data-editable="comment" 
                   data-location-id="${comment.location || locationId}"
                   data-review-id="${comment.review || comment.review_id}"
                   data-comment-id="${comment.id}" 
                   data-original-content="${comment.content || comment.formatted_content}">
                    ${comment.formatted_content || comment.content}
                </p>
                ${voteControls}
            </div>
        `;
        return div;
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    // Report functionality
    const reportButton = document.getElementById('reportButton');
    const reportModal = document.getElementById('reportModal');
    const closeReportModal = document.getElementById('closeReportModal');
    const cancelReport = document.getElementById('cancelReport');
    const reportForm = document.getElementById('reportForm');

    if (reportButton) {
        reportButton.addEventListener('click', () => {
            reportModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    }

    function closeReportModalFunc() {
        reportModal.style.display = 'none';
        document.body.style.overflow = '';
        reportForm.reset();
    }

    if (closeReportModal) {
        closeReportModal.addEventListener('click', closeReportModalFunc);
    }

    if (cancelReport) {
        cancelReport.addEventListener('click', closeReportModalFunc);
    }

    if (reportModal) {
        reportModal.addEventListener('click', (e) => {
            if (e.target === reportModal) {
                closeReportModalFunc();
            }
        });
    }

    if (reportForm) {
        reportForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                report_type: document.getElementById('reportType').value,
                description: document.getElementById('reportDescription').value
            };

            try {
                const response = await fetch(`/api/v1/viewing-locations/${locationId}/report/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(formData),
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to submit report');
                }

                const result = await response.json();
                
                // Show success message
                alert('Thank you for your report. It will be reviewed by our moderators.');
                closeReportModalFunc();
                
            } catch (error) {
                console.error('Report error:', error);
                alert(error.message || 'Failed to submit report. Please try again.');
            }
        });
    }

    function initializeCommentFormatting() {
        // Add event listeners to all formatting buttons
        document.addEventListener('click', function(e) {
            if (e.target.closest('.formatting-btn')) {
                e.preventDefault();
                const button = e.target.closest('.formatting-btn');
                const form = button.closest('.comment-form');
                const editableDiv = form.querySelector('.comment-input');
                
                // Focus the editor first
                editableDiv.focus();
                
                // Get the formatting type from button title
                const formatType = button.getAttribute('title').toLowerCase();
                
                // Apply formatting using simple execCommand
                applyFormattingSimple(formatType);
                
                // Update button states and hidden input
                setTimeout(() => {
                    updateButtonStates(form);
                    updateHiddenInput(editableDiv);
                }, 10);
            }
        });

        // Update button states when selection changes
        document.addEventListener('selectionchange', function() {
            const activeElement = document.activeElement;
            if (activeElement && activeElement.classList.contains('comment-input') && activeElement.contentEditable === 'true') {
                const form = activeElement.closest('.comment-form');
                updateButtonStates(form);
            }
        });
        
        // Update hidden input when content changes
        document.addEventListener('input', function(e) {
            if (e.target.classList.contains('comment-input') && e.target.contentEditable === 'true') {
                updateHiddenInput(e.target);
            }
        });
    }

    function applyFormattingSimple(formatType) {
        // Use document.execCommand for reliable formatting
        let command;
        switch(formatType) {
            case 'bold':
                command = 'bold';
                break;
            case 'italic':
                command = 'italic';
                break;
            case 'underline':
                command = 'underline';
                break;
            default:
                return;
        }
        
        // Apply the formatting
        document.execCommand(command, false, null);
    }

    function updateHiddenInput(editableDiv) {
        const form = editableDiv.closest('.comment-form');
        const hiddenInput = form.querySelector('.hidden-content');
        
        // Convert HTML content to markdown for storage
        const htmlContent = editableDiv.innerHTML;
        const markdownContent = htmlToMarkdown(htmlContent);
        
        // Debug logging to see the conversion
        console.log('HTML:', htmlContent);
        console.log('Markdown:', markdownContent);
        
        hiddenInput.value = markdownContent;
    }

    function htmlToMarkdown(html) {
        // Create a temporary div to work with the HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // Process the HTML content to extract formatting
        const result = processNodeForMarkdown(tempDiv);
        
        return result.trim();
    }
    
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

    function updateButtonStates(form) {
        if (!form) return;
        
        const buttons = form.querySelectorAll('.formatting-btn');
        
        buttons.forEach(button => {
            const formatType = button.getAttribute('title').toLowerCase();
            let command;
            
            switch(formatType) {
                case 'bold':
                    command = 'bold';
                    break;
                case 'italic':
                    command = 'italic';
                    break;
                case 'underline':
                    command = 'underline';
                    break;
                default:
                    return;
            }
            
            // Use queryCommandState to check if formatting is active
            const isActive = document.queryCommandState(command);
            button.classList.toggle('active', isActive);
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.ellipsis-menu-wrapper')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.style.display = 'none';
            });
        }
    });

    // Universal Editing System
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
                if (starContainer) {
                    initializeStarRatingForContainer(starContainer);
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
                'X-CSRFToken': csrfToken,
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
                
                // Recalculate and update metrics
                setTimeout(() => calculateRatingDistribution(), 100);
            }
            
            // Clean up edit mode
            cancelEdit(element, editControls);
        })
        .catch(error => {
            console.error('Error updating:', error);
            alert(`Failed to update ${type}. Please try again.`);
        });
    }
    
    function cancelEdit(element, editControls) {
        // Remove edit controls
        editControls.remove();
        
        // Show original content
        element.classList.remove('edit-mode');
    }

});