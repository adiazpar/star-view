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
        initializeCommentFormatting();
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
            // Handle comment reporting
            if (confirm('Report this comment for inappropriate content?')) {
                reportComment(commentId, reviewId, locationId);
            }
        }
    }
    
    // Delete a comment
    function deleteComment(commentId, reviewId, locationId) {
        fetch(`/api/v1/viewing-locations/${locationId}/reviews/${reviewId}/comments/${commentId}/`, {
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
    
    // Report a comment
    function reportComment(commentId, reviewId, locationId) {
        fetch(`/api/v1/viewing-locations/${locationId}/reviews/${reviewId}/comments/${commentId}/report/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': config.csrfToken,
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to report comment');
            }
            
            alert('Comment reported successfully. Thank you for helping keep our community safe.');
        })
        .catch(error => {
            console.error('Error reporting comment:', error);
            alert('Failed to report comment. Please try again.');
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
                <div class="comment-vote-controls">
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
                    ${comment.is_edited ? '<span class="edited-indicator">(edited)</span>' : ''}
                </div>
                <p class="comment-text" 
                   data-editable="comment" 
                   data-location-id="${comment.location || config.locationId}"
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
    
    // Initialize formatting functionality for comment forms
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

    // Apply formatting using execCommand
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
        let result = processNodeForMarkdown(tempDiv);
        
        // Handle multiple consecutive line breaks to preserve blank lines
        // Convert sequences of 2 or more line breaks to double line breaks
        result = result.replace(/\n{2,}/g, '\n\n');
        
        // Don't trim to preserve intentional blank lines at start/end
        return result;
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
                    // If div is empty or only contains whitespace, treat as blank line
                    if (!content.trim()) {
                        return '\n';
                    }
                    return content + '\n';
                default:
                    return content;
            }
        }
        
        return '';
    }

    // Update formatting button states
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