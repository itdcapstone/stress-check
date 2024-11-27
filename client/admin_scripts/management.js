let deleteUserId = null;

function confirmDeleteUser(event, username, userId) {
    event.preventDefault();  // Prevent default form behavior
    deleteUserId = userId;   // Save the user ID to delete
    const deleteMessage = document.getElementById('deleteMessage');
    deleteMessage.innerHTML = `Are you sure you want to delete user <strong>${username}</strong>?`;
    const modal = document.getElementById('deleteConfirmationModal');
    modal.classList.add('show');  // Show the custom modal
}

function closeModal() {
    const modal = document.getElementById('deleteConfirmationModal');
    modal.classList.remove('show');  // Hide the modal
    deleteUserId = null;  // Reset deleteUserId
}

function confirmDelete() {
    if (deleteUserId) {
        const deleteForm = document.getElementById('deleteForm');
        const userIdInput = deleteForm.querySelector('input[name="user_id"]');
        userIdInput.value = deleteUserId;
        deleteForm.submit();  // Submit the form programmatically
    }
    closeModal();  // Close the modal
}


window.onclick = function(event) {
    const modal = document.getElementById('deleteConfirmationModal');
    if (event.target === modal) {
        closeModal();
    }
}

// Simulate a successful user deletion
function deleteUser() {
    // Simulating a delete action with a success response
    setTimeout(() => {
        // After successful deletion, show a success message
        showCustomAlert('User has been successfully deleted!', true); // Show success alert
    }, 1000); // Simulating a delay for the delete action
}

// Call the deleteUser function when needed (like after clicking a delete button)
deleteUser();

function checkUserRole(event) {
    // Get the role from the button's data attribute
    const role = event.target.closest('button').getAttribute('data-role');
    const yearLevelField = document.querySelector('.input-group #year_level')?.closest('.input-group');

    // If the year level field is not found, don't proceed (optional safeguard)
    if (!yearLevelField) {
        console.warn('Year level field not found');
        return; // Early exit to avoid errors
    }

    // Check the role and show/hide "year level" input
    if (role === 'admin') {
        // Hide the "year level" input if the role is admin
        yearLevelField.style.display = 'none';
    } else {
        // Show the "year level" input if the role is not admin
        yearLevelField.style.display = 'block';
    }

    // Conditionally prevent default form submission
    // If you need to prevent submission only for certain conditions:
    if (someConditionToPreventFormSubmission) {
        event.preventDefault();
    } else {
        // Allow form submission
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const flashMessages = document.querySelectorAll('.custom-alert');
    flashMessages.forEach(function(alert) {
        // Add the active class to show the alert
        alert.classList.add('active');

        // Remove the active class after 3 seconds to hide the alert
        setTimeout(function() {
            alert.classList.add('fade-out');
            // After fade-out, remove the element entirely
            setTimeout(function() {
                alert.remove();
            }, 500); // Timeout duration matches the CSS transition time
        }, 3000); 
    });
});

function clearSearch() {
    // Clear the search input value
    document.getElementById('searchInput').value = '';
    // Submit the form to reset the search query
    document.querySelector('form').submit();
}




