const questions = document.querySelectorAll('.question-container');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const submitBtn = document.querySelector('.submit-btn');
const questionIndicator = document.getElementById('question-indicator');
let currentQuestion = 0;

function updateQuestionDisplay() {
    questions.forEach((question, index) => {
        question.classList.toggle('active', index === currentQuestion);
    });
    prevBtn.style.display = currentQuestion === 0 ? 'none' : 'inline';
    nextBtn.style.display = currentQuestion === questions.length - 1 ? 'none' : 'inline';
    submitBtn.style.display = currentQuestion === questions.length - 1 ? 'inline' : 'none';
    questionIndicator.textContent = `Question ${currentQuestion + 1} of ${questions.length}`;
}

document.addEventListener('DOMContentLoaded', function() {
    const questionHeadings = document.querySelectorAll('.question h2');
    questionHeadings.forEach(function(heading) {
        if (heading.innerText.length > 100 && heading.innerText.length <= 150) {
            heading.classList.add('long-question');
        } else if (heading.innerText.length > 150) {
            heading.classList.add('very-long-question');
        }
    });
});

function isAnswered() {
    const currentQuestionContainer = questions[currentQuestion];
    const inputs = currentQuestionContainer.querySelectorAll('input[type="radio"]');
    return Array.from(inputs).some(input => input.checked);
}

nextBtn.addEventListener('click', () => {
    if (isAnswered()) {
        // Proceed to next question
        if (currentQuestion < questions.length - 1) {
            currentQuestion++;
            updateQuestionDisplay();
        }
    } else {
        // Validation failed: shake the question container and show the alert
        const currentQuestionContainer = questions[currentQuestion];
        currentQuestionContainer.classList.add('shake');

        // Timeout to remove the shake effect after animation
        setTimeout(() => {
            currentQuestionContainer.classList.remove('shake');
        }, 500);

        // Show custom alert for unanswered question
        showCustomAlert('Please select an answer before proceeding.');
    }
});

prevBtn.addEventListener('click', () => {
    if (currentQuestion > 0) {
        currentQuestion--;
        updateQuestionDisplay();
    }
});

// Custom alert function
function showCustomAlert(message) {
    const alertBox = document.querySelector('.custom-alert.error-alert'); // Target the error alert box
    const alertMsg = alertBox.querySelector('.msg'); // Get the message span inside the alert

    // Set the custom message
    alertMsg.innerText = message;

    // Make the alert visible
    alertBox.classList.add('active');
    alertBox.classList.remove('fade-out'); // Ensure it doesn't have 'fade-out' when showing it


    setTimeout(() => {
        alertBox.classList.add('fade-out'); // Start fading out
        setTimeout(() => {
            alertBox.classList.remove('active'); // Hide the alert (but don't remove from DOM)
            alertBox.classList.remove('fade-out'); // Remove fade-out class so it can be reused
        }, 1000); 
    }, 1500); 
}

updateQuestionDisplay(); // Initial call to set up display