function applyHighlight(response, element, context) {
    // Define colors for each severity level
    const severityColors = {
        1: '#81C784',  // Light Green for low severity
        2: '#FFEB3B',  // Yellow for mild severity
        3: '#FFC107',  // Amber for moderate severity
        4: '#FF9800',  // Orange for high severity
        5: '#f44336'   // Red for critical severity
    };

    // Mapping for severity levels by context and response
    const mappings = {
        '6735a37be761ac9bd6d7abf2': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5}, // Sadness
        '6735a37ce761ac9bd6d7abf3': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5}, // Anxiety
        '6735a37ce761ac9bd6d7abf4': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5}, // Peer Pressure
        '6735a37ce761ac9bd6d7abf5': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5}, // Sleep Quality
        '6735a37ce761ac9bd6d7abf6': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5}, // AI Tools Impact
        '6735a37ce761ac9bd6d7abf7': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5}, // Family Stress
        '6735a37ce761ac9bd6d7abf8': {'Very Satisfied': 1, 'Satisfied': 2, 'Neutral': 3, 'Dissatisfied': 4, 'Very Dissatisfied': 5}, // Financial Satisfaction
        '6735a37ce761ac9bd6d7abf9': {'Strongly Agree': 1, 'Agree': 2, 'Neutral': 3, 'Disagree': 4, 'Strongly Disagree': 5}, // Friends Support
        '6735a37ce761ac9bd6d7abfa': {'Excellent': 1, 'Good': 2, 'Adequate': 3, 'Poor': 4, 'Very Poor': 5}, // Resources Access
        '6735a37ce761ac9bd6d7abfb': {'Strongly Disagree': 1, 'Disagree': 2, 'Neutral': 3, 'Agree': 4, 'Strongly Agree': 5}, // Home Stress
        '6735a37ce761ac9bd6d7abfc': {'Not at all': 1, 'A little': 2, 'Moderately': 3, 'Significantly': 4, 'Extremely': 5}, // Commute Stress
        '6735a37ce761ac9bd6d7abfd': {'Very Manageable': 1, 'Manageable': 2, 'Neutral': 3, 'Disturbing': 4, 'Very Disturbing': 5}, // Noise Level
        '6735a37ce761ac9bd6d7abfe': {'Strongly Disagree': 1, 'Disagree': 2, 'Neutral': 3, 'Agree': 4, 'Strongly Agree': 5}, // Weather Conditions
        '6735a37ce761ac9bd6d7abff': {'Yes': 1, 'No': 5}, // Program Confidence
        '6735a37ce761ac9bd6d7ac00': {'Not at all': 1, 'A little': 2, 'Moderately': 3, 'Significantly': 4, 'Extremely': 5}, // Academic Stress
        '6735a37ce761ac9bd6d7ac01': {'Completely': 1, 'Very Much': 2, 'Moderately': 3, 'Somewhat': 4, 'Not at all': 5} // Advisor Support
    };
    

    // Determine severity based on context and response
    const severity = mappings[context]?.[response] || 0;

    if (severity > 0) {
        element.style.borderLeftColor = severityColors[severity];
    } else {
        element.style.borderLeftColor = 'transparent'; // Default color if no severity
    }
}

// Apply the function to each card with data-response and data-context attributes
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.flow-card').forEach(card => {
        const response = card.getAttribute('data-response');
        const context = card.getAttribute('data-context');
        applyHighlight(response, card, context);
    });
});

function setProgress(level) {
    const progressCircle = document.querySelector('.progress-circle');
    const radius = progressCircle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (level / 5 * circumference);

    const levelColors = [
        "#4CAF50", // Level 1: Green (Low stress)
        "#FFC107", // Level 2: Yellow (Moderate stress)
        "#FF9800", // Level 3: Orange (High stress)
        "#FF5722", // Level 4: Dark Orange (Very high stress)
        "#F44336"  // Level 5: Red (Extreme stress)
    ];

    progressCircle.style.strokeDashoffset = offset;
    progressCircle.style.stroke = levelColors[level - 1];
}

const currentStressLevel = parseInt("{{ predicted_stress_level }}");
setProgress(currentStressLevel);

// Function to toggle the menu on mobile
function toggleMenu() {
    const menu = document.querySelector('.navbar-menu');
    const hamburger = document.querySelector('.hamburger');
    menu.classList.toggle('active');
    hamburger.classList.toggle('active');
}

async function generatePDF() {
    try {
        const element = document.getElementById('pdf-content');

        // Apply PDF-specific styling
        element.classList.add('pdf-mode');

        // Retrieve the stress level text from the existing display
        const stressLevelElement = document.getElementById('progress-number');
        const predictedStressLevel = stressLevelElement ? stressLevelElement.textContent : "N/A";

        // Hide progress circle and show plain text for PDF
        const progressCircle = document.querySelector('.progress-container');
        const stressText = document.createElement('div');
        stressText.className = 'stress-level-text';
        stressText.innerHTML = `<h2>Stress Level: ${predictedStressLevel} / 5</h2>`;
        progressCircle.replaceWith(stressText);

        const options = {
            margin: 10,
            filename: 'Stress_Test_Results.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: {
                scale: 3,
                useCORS: true
            },
            jsPDF: {
                unit: 'mm',
                format: 'a4',
                orientation: 'portrait'
            },
            pagebreak: { mode: ['css', 'avoid-all'] }
        };

        // Generate the PDF with html2pdf.js
        await html2pdf().set(options).from(element).save();

        // Revert to original layout after PDF generation
        stressText.replaceWith(progressCircle);
        element.classList.remove('pdf-mode');
    } catch (error) {
        console.error("Error generating PDF:", error);
        alert("An error occurred while generating the PDF. Please try again.");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const currentDate = new Date().toLocaleDateString(undefined, options);
    document.getElementById("test-date").innerText = currentDate;
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
