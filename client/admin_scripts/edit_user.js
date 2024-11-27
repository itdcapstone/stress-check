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