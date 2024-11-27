$(document).ready(function () {
    // Show related questions for the selected stressor
    $('#stressor').on('change', function () {
        const selectedStressor = $(this).val();
        $('.question-section').hide();
        $(`.question-section[data-stressor="${selectedStressor}"]`).show();
        fetchRecommendation();
    });

    // Fetch the recommendation when severity changes
    $('#severity').on('change', function () {
        fetchRecommendation();
    });

    function fetchRecommendation() {
        const stressor = $('#stressor').val();
        const severity = $('#severity').val();

        if (!stressor || !severity) return;

        $.ajax({
            url: "{{ url_for('get_recommendation') }}",
            method: 'GET',
            data: { stressor: stressor, severity: severity },
            success: function (response) {
                if (response.error) {
                    alert(response.error);
                    $('#current_text').val('');
                    $('#current_source').val('');
                } else {
                    $('#current_text').val(response.text);
                    $('#current_source').val(response.source);
                }
            },
            error: function () {
                alert('Failed to fetch recommendation. Please try again.');
            }
        });
    }
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
