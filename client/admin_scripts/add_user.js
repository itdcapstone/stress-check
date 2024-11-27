// JavaScript function to toggle forms
function toggleForm() {
    const role = document.getElementById('roleSelect').value;
    const userForm = document.getElementById('userForm');
    const adminForm = document.getElementById('adminForm');

    // Show/hide forms based on role selection
    if (role === 'user') {
        userForm.style.display = 'block';
        adminForm.style.display = 'none';
    } else if (role === 'admin') {
        userForm.style.display = 'none';
        adminForm.style.display = 'block';
    } else {
        userForm.style.display = 'none';
        adminForm.style.display = 'none';
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

    // Add event listeners to all toggle-password icons
    document.addEventListener('DOMContentLoaded', function () {
        const togglePasswordIcons = document.querySelectorAll('.toggle-password');

        togglePasswordIcons.forEach(icon => {
            icon.addEventListener('click', function () {
                const targetId = this.getAttribute('data-target');
                const passwordField = document.getElementById(targetId);

                // Toggle the input type between 'password' and 'text'
                const type = passwordField.type === 'password' ? 'text' : 'password';
                passwordField.type = type;

                // Toggle the icon class
                this.classList.toggle('bx-show');
                this.classList.toggle('bx-hide');
            });
        });
    });

    document.addEventListener('DOMContentLoaded', () => {
        const userForm = document.getElementById('userFormElement');
        const adminForm = document.getElementById('adminFormElement');
    
        // Reset user form after submission
        userForm.addEventListener('submit', () => {
            setTimeout(() => userForm.reset(), 100);
        });
    
        // Reset admin form after submission
        adminForm.addEventListener('submit', () => {
            setTimeout(() => adminForm.reset(), 100);
        });
    });
    

    