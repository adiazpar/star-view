/**
 * Account Profile Page JavaScript
 *
 * Handles all interactive functionality for the user profile page including:
 * - Profile picture upload/removal
 * - Name, email, and password updates
 * - Form validation and submission
 * - Success/error message display
 */

/**
 * Toggle password visibility for password input fields
 * @param {string} inputId - The ID of the password input element
 */
export function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === 'password' ? 'text' : 'password';

    // Toggle the eye icon
    const button = input.nextElementSibling;
    const eyeIcon = button.querySelector('.eye-icon');
    if (input.type === 'password') {
        eyeIcon.innerHTML = `
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
        `;
    } else {
        eyeIcon.innerHTML = `
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
        `;
    }
}

/**
 * Display a temporary message to the user
 * @param {string} message - The message text to display
 * @param {boolean} isError - Whether this is an error message
 */
function showMessage(message, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isError ? 'error' : 'success'}`;
    messageDiv.textContent = message;

    let messagesContainer = document.querySelector('.messages');
    if (!messagesContainer) {
        messagesContainer = document.createElement('div');
        messagesContainer.className = 'messages';
        document.body.appendChild(messagesContainer);
    }

    messagesContainer.appendChild(messageDiv);
    setTimeout(() => messageDiv.remove(), 3000);
}

/**
 * Get CSRF token from the page
 * @returns {string} The CSRF token value
 */
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

/**
 * Initialize profile picture management
 * @param {Object} urls - Object containing API endpoint URLs
 */
function initProfilePicture(urls) {
    const changePhotoBtn = document.getElementById('change-photo');
    const removePhotoBtn = document.getElementById('remove-photo');
    const profileUpload = document.getElementById('profile-upload');

    // Handle change photo
    changePhotoBtn.addEventListener('click', (e) => {
        e.preventDefault();
        profileUpload.click();
    });

    // Handle remove photo
    removePhotoBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (confirm('Are you sure you want to remove your profile picture?')) {
            fetch(urls.removeProfilePicture, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                },
                credentials: 'same-origin'
            })
            .then(async response => {
                const data = await response.json();
                if (response.ok) {
                    document.querySelector('.profile-image').src = data.default_image_url;
                } else {
                    alert('Error removing profile picture: ' + (data.detail || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error removing profile picture');
            });
        }
    });

    // Handle profile picture upload
    profileUpload.addEventListener('change', function(e) {
        if (this.files && this.files[0]) {
            const formData = new FormData();
            formData.append('profile_picture', this.files[0]);
            formData.append('csrfmiddlewaretoken', getCSRFToken());

            fetch(urls.uploadProfilePicture, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(async response => {
                const data = await response.json();
                if (response.ok) {
                    document.querySelector('.profile-image').src = data.image_url + '?t=' + new Date().getTime();
                } else {
                    alert('Error uploading image: ' + (data.detail || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error uploading image');
            });
        }
    });
}

/**
 * Initialize form submissions for name, email, and password updates
 * @param {Object} urls - Object containing API endpoint URLs
 */
function initFormHandlers(urls) {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formId = form.id;
            let url = '';

            const formData = new FormData(form);

            switch(formId) {
                case 'nameForm':
                    url = urls.updateName;
                    break;
                case 'emailForm':
                    url = urls.changeEmail;
                    break;
                case 'passwordForm':
                    url = urls.changePassword;
                    break;
                default:
                    return;
            }

            try {
                const response = await fetch(url, {
                    method: 'PATCH',
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(Object.fromEntries(formData))
                });

                const data = await response.json();
                if(response.ok) {
                    showMessage(data.detail);
                    if(formId === 'passwordForm') form.reset();
                }
                else {
                    showMessage(data.detail || 'An error occurred', true);
                }
            }
            catch (error) {
                showMessage('An error occurred while saving changes', true);
            }
        });
    });
}

/**
 * Initialize the profile page
 * @param {Object} config - Configuration object with API URLs
 */
export function initProfilePage(config) {
    initProfilePicture(config.urls);
    initFormHandlers(config.urls);
}

// Make togglePassword available globally for inline onclick handlers
window.togglePassword = togglePassword;
