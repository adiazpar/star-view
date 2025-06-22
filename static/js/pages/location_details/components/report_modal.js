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
            apiUrl = `/api/v1/viewing-locations/${currentReportTarget.locationId}/reviews/${currentReportTarget.id}/report/`;
        } else {
            apiUrl = `/api/v1/viewing-locations/${currentReportTarget.locationId}/reviews/${currentReportTarget.reviewId}/comments/${currentReportTarget.id}/report/`;
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