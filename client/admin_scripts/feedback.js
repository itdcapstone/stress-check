// Variables to hold the feedback ID and modal elements
let feedbackIdToDelete = null;
const modalUsername = document.getElementById('modalUsername');
const modalDate = document.getElementById('modalDate');
const modalUsernameDelete = document.getElementById('modalUsernameDelete');

// Function to open the modal for viewing feedback
function openModal(username, date, feedback) {
    const formattedDate = new Date(date).toLocaleString('en-GB', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
        hour12: false
    });

    // Insert the details into the view feedback modal
    modalUsername.innerText = username;
    modalDate.innerText = formattedDate;
    modalFeedback.innerText = feedback;

    document.getElementById('feedbackViewModal').style.display = 'block';
}

// Function to close the modal
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function openDeleteModal(feedbackId, username) {
    feedbackIdToDelete = feedbackId;  // Store the ID to delete
    console.log("Feedback ID to delete:", feedbackIdToDelete); // Debugging line

    modalUsernameDelete.innerText = username;

    const modal = document.getElementById('deleteConfirmationModal');
    modal.style.display = 'flex';
    modal.style.opacity = '1';
    modal.style.visibility = 'visible';
}




  function confirmDelete() {
    if (feedbackIdToDelete) {
        fetch('/admin/feedback/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ feedback_id: feedbackIdToDelete })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Server Response:", data); // Debugging line
            if (data.success) {
                // Successfully deleted
                document.getElementById(`feedback-row-${feedbackIdToDelete}`).remove();
                showToast(data.success, 'success');
            } else if (data.error) {
                // Error occurred
                showToast(data.error, 'error');
            }
            closeModal('deleteConfirmationModal');
        })
        .catch(error => {
            console.error('Fetch error:', error);
            showToast('An unexpected error occurred.', 'error');
        });
    }
}




// Event listener for delete buttons
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-feedback');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const feedbackId = this.getAttribute('data-id');
            const username = this.closest('tr').querySelector('td:nth-child(1)').textContent;
            openDeleteModal(feedbackId, username);
        });
    });

    const viewButtons = document.querySelectorAll('.view-feedback');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const username = this.getAttribute('data-username');
            const date = this.getAttribute('data-date');
            const feedback = this.getAttribute('data-feedback');
            openModal(username, date, feedback);
        });
    });
});

function showToast(message, type) {
    const toast = document.getElementById('toast');
    if (!toast) {
        console.error('Toast element not found!');
        return;
    }
    
    if (!message) {
        console.error('Toast message is undefined!');
        return;
    }

    toast.innerText = message;

    // Reset classes and add type class
    toast.className = '';
    toast.classList.add('show', type);

    // Auto-hide toast
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.classList.remove('show', 'fade-out');
            toast.innerText = ''; // Clear message after hiding
        }, 500); // Fade-out duration
    }, 3000); // Show duration
}


