function setProgress(level) {
    const progressCircle = document.querySelector('.progress-circle');
    const radius = progressCircle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    const maxLevel = 5;  // Stress level goes from 1 to 5
    const offset = circumference - (level / maxLevel * circumference);

    // Colors for each stress level: from green to red
    const levelColors = [
        "#4CAF50", // Level 1: Green (Low stress)
        "#FFC107", // Level 2: Yellow (Moderate stress)
        "#FF9800", // Level 3: Orange (High stress)
        "#FF5722", // Level 4: Dark Orange (Very high stress)
        "#F44336"  // Level 5: Red (Extreme stress)
    ];

    // Update the stroke-dashoffset and color based on the stress level
    progressCircle.style.strokeDashoffset = offset;
    progressCircle.style.stroke = levelColors[level - 1];
}

// Set the current stress level (from 1 to 5, dynamically fetched from backend)
const currentStressLevel = parseInt("{{ assessment.stress_level }}");
setProgress(currentStressLevel);