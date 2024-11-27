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