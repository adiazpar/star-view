/**
 * PhotoGallery Component
 * Handles photo display and upload functionality for viewing locations
 */
export class PhotoGallery {
    constructor(locationId, options = {}) {
        this.locationId = locationId;
        this.container = options.container || document.getElementById('photo-gallery');
        this.photos = [];
        this.primaryPhotoId = null;
        this.isAuthenticated = options.isAuthenticated || false;
        this.isOwner = options.isOwner || false;
        this.currentUsername = options.currentUsername || null;
        this.csrfToken = options.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        this.initialize();
    }

    async initialize() {
        if (!this.container) return;
        
        await this.loadPhotos();
        this.render();
        this.attachEventListeners();
    }

    async loadPhotos() {
        try {
            const response = await fetch(`/api/v1/viewing-locations/${this.locationId}/photos/`, {
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load photos');
            }
            
            const data = await response.json();
            this.photos = data.results || data;
            this.primaryPhotoId = this.photos.find(p => p.is_primary)?.id;
        } catch (error) {
            console.error('Error loading photos:', error);
            this.photos = [];
        }
    }

    render() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="photo-gallery-wrapper">
                ${this.renderHeader()}
                ${this.renderPhotos()}
                ${this.renderUploadModal()}
            </div>
        `;
    }

    renderHeader() {
        return `
            <div class="photo-gallery-header">
                <h4>Location Photos</h4>
                ${this.isAuthenticated ? `
                    <button class="btn-upload-photo" id="openUploadModal">
                        <i class="fas fa-camera"></i> Add Photo
                    </button>
                ` : ''}
            </div>
        `;
    }

    renderPhotos() {
        if (this.photos.length === 0) {
            return `
                <div class="no-photos">
                    <i class="fas fa-image"></i>
                    <p>No photos yet</p>
                    ${this.isAuthenticated ? '<p class="text-muted">Be the first to add a photo!</p>' : ''}
                </div>
            `;
        }

        return `
            <div class="photo-grid">
                ${this.photos.map(photo => this.renderPhotoCard(photo)).join('')}
            </div>
        `;
    }

    renderPhotoCard(photo) {
        const isPrimary = photo.id === this.primaryPhotoId;
        
        return `
            <div class="photo-card ${isPrimary ? 'primary' : ''}" data-photo-id="${photo.id}">
                <div class="photo-wrapper">
                    <img src="${photo.thumbnail_url || photo.image_url}" alt="${photo.caption || 'Location photo'}" 
                         loading="lazy" class="photo-image" data-full-size="${photo.image_url}">
                    ${isPrimary ? '<span class="primary-badge">Primary</span>' : ''}
                    <div class="photo-actions">
                        ${this.isOwner && !isPrimary ? `
                            <button class="btn-set-primary" data-photo-id="${photo.id}" 
                                    title="Set as primary photo">
                                <i class="fas fa-star"></i>
                            </button>
                        ` : ''}
                        ${(this.isOwner || photo.uploaded_by_username === this.getCurrentUsername()) ? `
                            <button class="btn-delete-photo" data-photo-id="${photo.id}" 
                                    title="Delete photo">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
                ${photo.caption ? `<p class="photo-caption">${photo.caption}</p>` : ''}
                <div class="photo-meta">
                    <span class="photo-author">
                        <i class="fas fa-user"></i> ${photo.uploaded_by_username || 'Unknown'}
                    </span>
                    <span class="photo-date">
                        <i class="fas fa-calendar"></i> ${this.formatDate(photo.uploaded_at || photo.created_at)}
                    </span>
                </div>
            </div>
        `;
    }

    renderUploadModal() {
        return `
            <div class="photo-upload-modal" id="photoUploadModal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Upload Photo</h3>
                        <button class="modal-close" id="closeUploadModal">&times;</button>
                    </div>
                    <form id="photoUploadForm" class="photo-upload-form">
                        <div class="form-group">
                            <label for="photoFile">Select Photo</label>
                            <input type="file" id="photoFile" name="image" accept="image/*" required>
                            <div class="file-preview" id="filePreview"></div>
                        </div>
                        <div class="form-group">
                            <label for="photoCaption">Caption (optional)</label>
                            <textarea id="photoCaption" name="caption" rows="3" 
                                      placeholder="Describe this photo..."></textarea>
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn-cancel" id="cancelUpload">Cancel</button>
                            <button type="submit" class="btn-primary" id="submitUpload">
                                <i class="fas fa-upload"></i> Upload Photo
                            </button>
                        </div>
                        <div class="upload-progress" id="uploadProgress" style="display: none;">
                            <div class="progress-bar">
                                <div class="progress-fill" id="progressFill"></div>
                            </div>
                            <p class="progress-text">Uploading...</p>
                        </div>
                    </form>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        // Upload modal controls
        const openBtn = document.getElementById('openUploadModal');
        const closeBtn = document.getElementById('closeUploadModal');
        const cancelBtn = document.getElementById('cancelUpload');
        const modal = document.getElementById('photoUploadModal');
        const form = document.getElementById('photoUploadForm');
        const fileInput = document.getElementById('photoFile');

        if (openBtn) {
            openBtn.addEventListener('click', () => this.openUploadModal());
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeUploadModal());
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeUploadModal());
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeUploadModal();
                }
            });
        }

        if (form) {
            form.addEventListener('submit', (e) => this.handleUpload(e));
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.previewFile(e));
        }

        // Photo interactions
        const photoImages = this.container.querySelectorAll('.photo-image');
        photoImages.forEach(img => {
            img.addEventListener('click', (e) => this.openLightbox(e));
        });

        // Set primary buttons
        const setPrimaryBtns = this.container.querySelectorAll('.btn-set-primary');
        setPrimaryBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.setPrimaryPhoto(e));
        });

        // Delete photo buttons
        const deleteBtns = this.container.querySelectorAll('.btn-delete-photo');
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.deletePhoto(e));
        });
    }

    openUploadModal() {
        const modal = document.getElementById('photoUploadModal');
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    closeUploadModal() {
        const modal = document.getElementById('photoUploadModal');
        const form = document.getElementById('photoUploadForm');
        const preview = document.getElementById('filePreview');
        
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
        
        if (form) {
            form.reset();
        }
        
        if (preview) {
            preview.innerHTML = '';
        }
    }

    previewFile(event) {
        const file = event.target.files[0];
        const preview = document.getElementById('filePreview');
        
        if (!file || !preview) return;
        
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            };
            reader.readAsDataURL(file);
        }
    }

    async handleUpload(event) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const progressBar = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const submitBtn = document.getElementById('submitUpload');
        
        if (progressBar) progressBar.style.display = 'block';
        if (submitBtn) submitBtn.disabled = true;
        
        try {
            const response = await fetch(`/api/v1/viewing-locations/${this.locationId}/upload_photo/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                },
                body: formData,
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }
            
            const photo = await response.json();
            
            // Update UI
            this.photos.push(photo);
            this.render();
            this.attachEventListeners();
            this.closeUploadModal();
            
            // Show success message
            this.showMessage('Photo uploaded successfully!', 'success');
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showMessage(error.message || 'Failed to upload photo', 'error');
        } finally {
            if (progressBar) progressBar.style.display = 'none';
            if (submitBtn) submitBtn.disabled = false;
            if (progressFill) progressFill.style.width = '0%';
        }
    }

    async setPrimaryPhoto(event) {
        event.stopPropagation();
        
        const photoId = event.currentTarget.dataset.photoId;
        
        try {
            const response = await fetch(`/api/v1/viewing-locations/${this.locationId}/set_primary_photo/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ photo_id: photoId }),
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Failed to set primary photo');
            }
            
            // Update UI
            this.primaryPhotoId = parseInt(photoId);
            this.render();
            this.attachEventListeners();
            
            this.showMessage('Primary photo updated!', 'success');
            
        } catch (error) {
            console.error('Error setting primary photo:', error);
            this.showMessage('Failed to update primary photo', 'error');
        }
    }

    openLightbox(event) {
        const imgSrc = event.target.dataset.fullSize || event.target.src;
        const lightbox = document.createElement('div');
        lightbox.className = 'photo-lightbox';
        lightbox.innerHTML = `
            <div class="lightbox-content">
                <span class="lightbox-close">&times;</span>
                <img src="${imgSrc}" alt="Full size photo">
            </div>
        `;
        
        document.body.appendChild(lightbox);
        document.body.style.overflow = 'hidden';
        
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox || e.target.className === 'lightbox-close') {
                document.body.removeChild(lightbox);
                document.body.style.overflow = '';
            }
        });
    }

    showMessage(message, type = 'info') {
        const messageEl = document.createElement('div');
        messageEl.className = `gallery-message ${type}`;
        messageEl.textContent = message;
        
        this.container.appendChild(messageEl);
        
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }

    async deletePhoto(event) {
        event.stopPropagation();
        
        const photoId = event.currentTarget.dataset.photoId;
        
        if (!confirm('Are you sure you want to delete this photo?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/v1/viewing-locations/${this.locationId}/delete_photo/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ photo_id: photoId }),
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete photo');
            }
            
            const result = await response.json();
            
            // Remove photo from array
            this.photos = this.photos.filter(p => p.id !== parseInt(photoId));
            
            // If it was the primary photo, clear the primary photo ID
            if (result.was_primary) {
                this.primaryPhotoId = null;
            }
            
            // Re-render the gallery
            this.render();
            this.attachEventListeners();
            
            this.showMessage('Photo deleted successfully!', 'success');
            
        } catch (error) {
            console.error('Error deleting photo:', error);
            this.showMessage(error.message || 'Failed to delete photo', 'error');
        }
    }

    getCurrentUsername() {
        // Return stored username if available
        if (this.currentUsername) {
            return this.currentUsername;
        }
        
        // Fallback: Try to get current username from various sources
        const mapContainer = document.querySelector('.map-container');
        if (mapContainer && mapContainer.dataset.currentUser === 'true') {
            // Try to get from a user menu or profile element
            const userMenu = document.querySelector('[data-username]');
            if (userMenu) {
                return userMenu.dataset.username;
            }
            
            // Try to get from any element that might contain the username
            const usernameElement = document.querySelector('.username, .user-name, [data-user-name]');
            if (usernameElement) {
                return usernameElement.textContent || usernameElement.dataset.userName;
            }
        }
        return null;
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown date';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return 'Invalid date';
            
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return 'Invalid date';
        }
    }
}