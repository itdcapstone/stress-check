 // JavaScript Code for Modal and Recommendations
 document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("recommendationModal");
    const closeModal = modal.querySelector(".close");
    modal.style.display = "none";

    function showModal(stressorName, recommendations) {
        document.getElementById('modal-stressor-name').textContent = stressorName;
        const recommendationList = document.getElementById('modal-recommendations');
        recommendationList.innerHTML = '';

        // Populate recommendations
        if (recommendations.length > 0) {
            recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec.text;
                recommendationList.appendChild(li);
            });
        } else {
            const noRecommendationItem = document.createElement('li');
            noRecommendationItem.textContent = "No recommendations available.";
            recommendationList.appendChild(noRecommendationItem);
        }

        // Set source info
        const sourceElement = document.querySelector('.source-tooltip');
        const source = recommendations[0]?.source || 'Source not available';
        sourceElement.textContent = source;
        modal.style.display = "flex";
    }

    document.querySelector('.result-container').addEventListener('click', function (event) {
        const stressorItem = event.target.closest('.stressor-item');
        if (stressorItem) {
            const stressorName = stressorItem.getAttribute('data-stressor');
            const recommendationsStr = stressorItem.getAttribute('data-recommendations');
            let recommendations = [];

            // Parse recommendations safely
            try {
                recommendations = JSON.parse(recommendationsStr);
            } catch (error) {
                recommendations = [];
            }

            showModal(stressorName, recommendations);
        }
    });

    // Close modal when close button or outside modal is clicked
    closeModal.addEventListener('click', function () {
        modal.style.display = "none";
    });

    modal.addEventListener('click', function (event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
});


function setProgress(level) {
    const progressCircle = document.querySelector('.progress-circle');
    const radius = progressCircle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const maxLevel = 5;
    const offset = circumference - (level / maxLevel * circumference);

    const levelColors = [
        "#4CAF50", "#FFC107", "#FF9800", "#FF5722", "#F44336"
    ];

    progressCircle.style.strokeDashoffset = offset;
    progressCircle.style.stroke = levelColors[level - 1];
}

const currentStressLevel = parseInt("{{ predicted_stress_level }}", 10);
setProgress(currentStressLevel);

// JavaScript to toggle centered modal when sidebar is collapsed
document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const modalContent = document.querySelector('.result-container .modal .modal-content');

    // Function to check and apply center positioning
    function centerModal() {
        if (body.classList.contains('sidebar-collapsed')) {
            modalContent.style.marginLeft = '50%';
            modalContent.style.transform = 'translateX(-50%)';
        } else {
            // Reset styles if the sidebar is not collapsed
            modalContent.style.marginLeft = '';
            modalContent.style.transform = '';
        }
    }

    // Add an event listener to toggle the 'sidebar-collapsed' class and recheck centering
    document.querySelector('#sidebar-toggle-button').addEventListener('click', () => {
        body.classList.toggle('sidebar-collapsed');
        centerModal();
    });

    // Initial check
    centerModal();
});
