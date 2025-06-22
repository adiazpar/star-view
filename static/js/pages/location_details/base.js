// Location Details - Main Orchestrator
document.addEventListener('DOMContentLoaded', function() {
    // Get configuration and utilities
    const utils = window.LocationDetailsUtils;
    const config = utils.getConfig();
    
    // Validate configuration
    if (!utils.validateConfig(config)) {
        console.error('Invalid configuration - some components may not work properly');
        return;
    }
    
    // Add CSRF token to config
    config.csrfToken = utils.getCsrfToken();
    
    // Create event bus for component communication
    const eventBus = utils.createEventBus();
    
    // Initialize all components
    initializeComponents(config, eventBus);
    
    // Initialize non-componentized features
    initializeRemainingFeatures(config, eventBus);
});

function initializeComponents(config, eventBus) {
    // Initialize core systems in order of dependency
    if (window.EditingSystem) {
        window.EditingSystem.init(config, eventBus);
    }
    
    if (window.VotingSystem) {
        window.VotingSystem.init(config, eventBus);
    }
    
    if (window.ReviewSystem) {
        window.ReviewSystem.init(config, eventBus);
    }
    
    if (window.CommentSystem) {
        window.CommentSystem.init(config, eventBus);
    }
    
    if (window.ImageUploadSystem) {
        window.ImageUploadSystem.init();
    }
    
    console.log('Location details components initialized');
}

function initializeRemainingFeatures(config, eventBus) {
    // Initialize Photo Gallery and Carousel
    loadPhotosAndInitialize(config);
    
    // Initialize favorite functionality
    if (config.isAuthenticated) {
        initializeFavoriteSystem(config);
    }
    
    // Initialize report system
    initializeReportSystem(config);
}

// Photo Gallery and Carousel functionality (to be moved to separate component later)
async function loadPhotosAndInitialize(config) {
    const utils = window.LocationDetailsUtils;
    
    try {
        const response = await fetch(`/api/v1/viewing-locations/${config.locationId}/photos/`, {
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.json();
            const photos = data.results || data;
            
            initializeHeroCarousel(photos, config);
            initializePhotosGrid(photos, config);
            
            if (config.isAuthenticated) {
                initializeUploadModal(config);
            }
        }
    } catch (error) {
        console.error('Error loading photos:', error);
        initializeHeroCarousel([], config);
        initializePhotosGrid([], config);
    }
}

function initializeHeroCarousel(photos, config) {
    const carouselContent = document.getElementById('carouselContent');
    const photoCredit = document.getElementById('photoCredit');
    const prevBtn = document.getElementById('carouselPrev');
    const nextBtn = document.getElementById('carouselNext');
    
    if (!photos || photos.length === 0) {
        // Show default map view
        carouselContent.innerHTML = `
            <div class="carousel-slide active">
                <img src="https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v11/static/${config.locationLongitude},${config.locationLatitude},13/1200x500@2x?access_token=${config.mapboxToken}"
                     alt="Map view of ${config.locationName}">
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
            photoCredit.innerHTML = `Photo by ${currentPhoto.uploaded_by_username || 'Unknown'} • ${window.LocationDetailsUtils.formatDate(currentPhoto.uploaded_at || currentPhoto.created_at)}`;
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

function initializePhotosGrid(photos, config) {
    const photosGrid = document.getElementById('photosGrid');
    const photosTitle = document.getElementById('photosTitle');
    
    photosTitle.textContent = `Photos (${photos.length})`;
    
    if (!photos || photos.length === 0) {
        photosGrid.innerHTML = `
            <div class="no-photos" style="grid-column: 1 / -1; text-align: center; padding: var(--space-xl); color: var(--text-tertiary);">
                <i class="fas fa-image" style="font-size: 3rem; margin-bottom: var(--space-md); opacity: 0.5;"></i>
                <p>No photos yet</p>
                ${config.isAuthenticated ? '<p class="text-muted">Be the first to add a photo!</p>' : ''}
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

function initializeUploadModal(config) {
    const uploadBtn = document.getElementById('openUploadModal');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            // Create and show upload modal
            const modal = createUploadModal(config);
            document.body.appendChild(modal);
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    }
}

function createUploadModal(config) {
    const utils = window.LocationDetailsUtils;
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
            const response = await fetch(`/api/v1/viewing-locations/${config.locationId}/upload_photo/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': config.csrfToken
                },
                body: formData,
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                closeModal();
                // Reload photos
                loadPhotosAndInitialize(config);
                utils.showMessage('Photo uploaded successfully!', 'success');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            utils.showMessage(error.message || 'Failed to upload photo', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Photo';
        }
    });
    
    return modal;
}

// Global functions for photo lightbox
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

// Favorite functionality
function initializeFavoriteSystem(config) {
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
    const favoriteButton = document.querySelector('.favorite-button');
    if (favoriteButton) {
        fetch(`/api/v1/viewing-locations/${config.locationId}/favorite/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': config.csrfToken,
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

            fetch(`/api/v1/viewing-locations/${config.locationId}/${endpoint}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': config.csrfToken,
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

// Report functionality
function initializeReportSystem(config) {
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
                const response = await fetch(`/api/v1/viewing-locations/${config.locationId}/report/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': config.csrfToken
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
}