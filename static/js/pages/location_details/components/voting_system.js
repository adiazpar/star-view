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
    
    // Setup event listeners for voting functionality
    function setupEventListeners() {
        const reviewsList = document.querySelector('.reviews-list');
        if (reviewsList) {
            reviewsList.addEventListener('click', handleVoteClick);
        }
    }
    
    // Handle vote button clicks
    function handleVoteClick(e) {
        const voteButton = e.target.closest('.vote-button');
        if (voteButton && !voteButton.classList.contains('disabled')) {
            e.preventDefault();
            processVote(voteButton);
        }
    }
    
    // Process a vote action
    function processVote(voteButton) {
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
                'X-CSRFToken': config.csrfToken,
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
            updateVoteDisplay(voteContainer, data);
            
            // Emit event for other components that might need to know
            if (eventBus) {
                eventBus.emit('voteUpdated', {
                    type: isCommentVote ? 'comment' : 'review',
                    id: isCommentVote ? commentId : reviewId,
                    voteData: data
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to register vote. Please try again.');
        });
    }
    
    // Update vote display after successful vote
    function updateVoteDisplay(voteContainer, data) {
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
    }
    
    // Get vote counts for a specific item
    function getVoteCounts(type, id) {
        const selector = type === 'comment' 
            ? `[data-comment-id="${id}"] .comment-vote-controls`
            : `[data-review-id="${id}"] .vote-controls`;
            
        const voteContainer = document.querySelector(selector);
        if (!voteContainer) return null;
        
        const upvoteCount = voteContainer.querySelector('.upvote-count');
        const downvoteCount = voteContainer.querySelector('.downvote-count');
        
        return {
            upvotes: upvoteCount ? parseInt(upvoteCount.textContent) : 0,
            downvotes: downvoteCount ? parseInt(downvoteCount.textContent) : 0
        };
    }
    
    // Set vote button states programmatically
    function setVoteButtonState(type, id, userVote, voteCounts) {
        const selector = type === 'comment' 
            ? `[data-comment-id="${id}"] .comment-vote-controls`
            : `[data-review-id="${id}"] .vote-controls`;
            
        const voteContainer = document.querySelector(selector);
        if (!voteContainer) return;
        
        updateVoteDisplay(voteContainer, {
            user_vote: userVote,
            upvotes: voteCounts.upvotes,
            downvotes: voteCounts.downvotes
        });
    }
    
    // Disable voting for specific item (used when user owns the content)
    function disableVoting(type, id) {
        const selector = type === 'comment' 
            ? `[data-comment-id="${id}"] .vote-button`
            : `[data-review-id="${id}"] .vote-button`;
            
        const voteButtons = document.querySelectorAll(selector);
        voteButtons.forEach(button => {
            button.classList.add('disabled');
            button.disabled = true;
        });
    }
    
    // Enable voting for specific item
    function enableVoting(type, id) {
        const selector = type === 'comment' 
            ? `[data-comment-id="${id}"] .vote-button`
            : `[data-review-id="${id}"] .vote-button`;
            
        const voteButtons = document.querySelectorAll(selector);
        voteButtons.forEach(button => {
            button.classList.remove('disabled');
            button.disabled = false;
        });
    }
    
    // Public API
    return {
        init: init,
        getVoteCounts: getVoteCounts,
        setVoteButtonState: setVoteButtonState,
        disableVoting: disableVoting,
        enableVoting: enableVoting
    };
})();