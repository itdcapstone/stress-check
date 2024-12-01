 // Toggle password visibility
 function togglePasswordVisibility() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('togglePassword');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text'; // Show password
        toggleIcon.classList.remove('bxs-show'); // Change to hide icon
        toggleIcon.classList.add('bxs-hide'); 
    } else {
        passwordInput.type = 'password'; // Hide password
        toggleIcon.classList.remove('bxs-hide'); // Change back to show icon
        toggleIcon.classList.add('bxs-show');
    }
}
document.getElementById('adminLoginForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const formData = new FormData(this);

    fetch('/admin_login', { 
        method: 'POST', 
        body: formData 
    })
    .then(response => {
        if (response.ok) {
            return response.json(); // Parse JSON for successful responses
        }
        // Handle the case when response is not OK (error handling)
        return response.json().then(data => {
            throw new Error(data.error || 'Unexpected error occurred');
        });
    })
    .then(data => {
        if (data.success) {
            // If successful login, store success message and redirect
            sessionStorage.setItem('success_message', data.success);
            window.location.href = data.redirect_url;  // Redirect to dashboard
        }
    })
    .catch(error => {
        // Show error message in a toast
        showToast(error.message, 'error');
    });
});


// Function to show toast messages
function showToast(message, type) {
    const toast = document.getElementById('toast');
    if (!toast) {
        console.error('Toast element not found!');
        return;
    }

    // Set the message
    toast.innerText = message;

    // Remove any existing classes first
    toast.classList.remove('show', 'success', 'error', 'fade-out');

    // Add the correct type class (either success or error)
    toast.classList.add('show', type);

    // Set the toast to fade out after 3 seconds
    setTimeout(() => {
        toast.classList.add('fade-out'); // Apply fade-out after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show', 'fade-out'); // Remove the show and fade-out after 500ms
            toast.innerText = ''; // Clear the message
        }, 500); // Match this with the fade-out animation duration
    }, 3000); // Show toast for 3 seconds
}