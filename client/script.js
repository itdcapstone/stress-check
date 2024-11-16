const allSideMenu = document.querySelectorAll('#sidebar .side-menu.top li a');

allSideMenu.forEach(item=> {
	const li = item.parentElement;

	item.addEventListener('click', function () {
		allSideMenu.forEach(i=> {
			i.parentElement.classList.remove('active');
		})
		li.classList.add('active');
	})
});



// TOGGLE SIDEBAR
const menuBar = document.querySelector('#content nav .bx.bx-menu');
const sidebar = document.getElementById('sidebar');

menuBar.addEventListener('click', function () {
	sidebar.classList.toggle('hide');
})

const searchButton = document.querySelector('#content nav form .form-input button');
const searchButtonIcon = document.querySelector('#content nav form .form-input button .bx');
const searchForm = document.querySelector('#content nav form');

searchButton.addEventListener('click', function (e) {
	if(window.innerWidth < 576) {
		e.preventDefault();
		searchForm.classList.toggle('show');
		if(searchForm.classList.contains('show')) {
			searchButtonIcon.classList.replace('bx-search', 'bx-x');
		} else {
			searchButtonIcon.classList.replace('bx-x', 'bx-search');
		}
	}
})





if(window.innerWidth < 768) {
	sidebar.classList.add('hide');
} else if(window.innerWidth > 576) {
	searchButtonIcon.classList.replace('bx-x', 'bx-search');
	searchForm.classList.remove('show');
}


window.addEventListener('resize', function () {
	if(this.innerWidth > 576) {
		searchButtonIcon.classList.replace('bx-x', 'bx-search');
		searchForm.classList.remove('show');
	}
})


const switchMode = document.getElementById('switch-mode');

switchMode.addEventListener('change', function () {
	if(this.checked) {
		document.body.classList.add('dark');
	} else {
		document.body.classList.remove('dark');
	}
})

// Profile.html
document.addEventListener('DOMContentLoaded', function () {
    const editLink = document.getElementById('edit-profile-link');
    const submitButton = document.getElementById('submit-button');
    const cancelButton = document.getElementById('cancel-button');
    const formButtons = document.getElementById('form-buttons');
    
    const formFields = document.querySelectorAll('.profile-container input, .profile-container select');

    const saveModal = document.getElementById('save-modal');
    const cancelModal = document.getElementById('cancel-modal');
    const closeSaveModal = document.getElementById('close-save-modal');
    const closeCancelModal = document.getElementById('close-cancel-modal');
    const confirmCancel = document.getElementById('confirm-cancel');
    const cancelModalButton = document.getElementById('cancel-modal-button');

    // Enable edit mode
    editLink.addEventListener('click', (e) => {
        e.preventDefault();
        formButtons.style.display = 'flex';
        formFields.forEach(field => field.disabled = false);
    });

    // Save changes and show save modal
    submitButton.addEventListener('click', (e) => {
        // Prevent default form submission (so we can enable fields first)
        e.preventDefault();
    
        // Enable all form fields before submitting
        formFields.forEach(field => field.disabled = false);
    
        // Submit the form programmatically after enabling fields
        document.getElementById('profile-form').submit();
    
        // Show save modal
        saveModal.style.display = 'block';
        formButtons.style.display = 'none';
        formFields.forEach(field => field.disabled = true); // Disable fields again after submitting
    });
    // Cancel edits and show cancel modal
    cancelButton.addEventListener('click', () => {
        cancelModal.style.display = 'block';
    });

    // Confirm cancel action in the modal
    confirmCancel.addEventListener('click', () => {
        cancelModal.style.display = 'none';
        formButtons.style.display = 'none';
        formFields.forEach(field => field.disabled = true);
    });

    // Close modals
    closeSaveModal.onclick = () => saveModal.style.display = 'none';
    closeCancelModal.onclick = () => cancelModal.style.display = 'none';
    cancelModalButton.onclick = () => cancelModal.style.display = 'none';

    // Close modals if clicking outside
    window.onclick = (event) => {
        if (event.target == saveModal) {
            saveModal.style.display = 'none';
        }
        if (event.target == cancelModal) {
            cancelModal.style.display = 'none';
        }
    };
});

// change email
document.addEventListener('DOMContentLoaded', function () {
    const changeEmailModal = document.getElementById('change-email-modal');
    const changeEmailButton = document.querySelector('.change-button');
    const closeChangeEmailModal = document.getElementById('close-change-email-modal');
    const passwordField = document.getElementById('email-password');
    const errorMessageDiv = document.createElement('div');
    errorMessageDiv.id = 'password-error-message'; // Create the error message div
    
    // Show the email change modal
    changeEmailButton.addEventListener('click', function () {
        console.log("Change Email button clicked"); // For debugging
        changeEmailModal.style.display = 'block';
    });

    // Close the modal when "X" is clicked
    closeChangeEmailModal.addEventListener('click', function () {
        changeEmailModal.style.display = 'none';
    });

    // Close the modal when clicking outside the modal content
    window.addEventListener('click', function (event) {
        if (event.target === changeEmailModal) {
            changeEmailModal.style.display = 'none';
        }
    });

    // Check password on form submit
    const changeEmailForm = document.getElementById('change-email-form');
    changeEmailForm.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent form from submitting initially

        // Clear any previous error messages
        const existingErrorMessage = document.getElementById('password-error-message');
        if (existingErrorMessage) {
            existingErrorMessage.remove();
        }

        const password = passwordField.value;

        // Fetch the actual password from the server using AJAX or by including it in the response
        fetch('/check_password', {
            method: 'POST',
            body: JSON.stringify({ password: password }),
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                // Show error message
                errorMessageDiv.textContent = "Incorrect password. Please try again.";
                passwordField.parentNode.appendChild(errorMessageDiv);

                // Shake the password input field
                passwordField.classList.add('shake');
                setTimeout(() => {
                    passwordField.classList.remove('shake');
                }, 500); // Remove the shake after 500ms
            } else {
                // Proceed with form submission if password is correct
                changeEmailForm.submit();
            }
        });
    });
});


// Change Password
document.addEventListener('DOMContentLoaded', function () {
    const changePasswordModal = document.getElementById('change-password-modal');
    const changePasswordButton = document.querySelector('.change-password-button');
    const closeChangePasswordModal = document.getElementById('close-change-password-modal');
    
    const currentPasswordField = document.getElementById('current-password');
    const newPasswordField = document.getElementById('new-password');
    const confirmNewPasswordField = document.getElementById('confirm-new-password');
    const currentPasswordError = document.getElementById('current-password-error');

    changePasswordButton.addEventListener('click', function () {
        changePasswordModal.style.display = 'block';
    });

    closeChangePasswordModal.addEventListener('click', function () {
        changePasswordModal.style.display = 'none';
    });

    window.addEventListener('click', function (event) {
        if (event.target === changePasswordModal) {
            changePasswordModal.style.display = 'none';
        }
    });

    // Add the submit event listener here
    const changePasswordForm = document.getElementById('change-password-form');
    changePasswordForm.addEventListener('submit', function (e) {
        e.preventDefault();

        currentPasswordError.style.display = 'none';

        const currentPassword = currentPasswordField.value;
        const newPassword = newPasswordField.value;
        const confirmNewPassword = confirmNewPasswordField.value;

        if (newPassword !== confirmNewPassword) {
            confirmNewPasswordField.setCustomValidity("Passwords do not match.");
            confirmNewPasswordField.reportValidity();
            return;
        } else {
            confirmNewPasswordField.setCustomValidity("");
        }

        fetch('/check_password', {
            method: 'POST',
            body: JSON.stringify({ password: currentPassword }),
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                currentPasswordError.style.display = 'block';
                currentPasswordError.textContent = data.message || "Incorrect current password.";
            } else {
                // Submit the form to update the password if the password verification succeeded
                changePasswordForm.submit();
            }
        })
        .catch(error => console.error('Error:', error));
    });
});


function confirmDelete(username) {
    if (confirm(`Are you sure you want to delete the user '${username}'?`)) {
        // If user confirms, submit the form
        document.querySelector('.edit-delete-form').submit();
    }
}


//questionnaires
document.addEventListener("DOMContentLoaded", function() {
    fetch('/test_stress')
        .then(response => response.json())
        .then(data => {
            const questionsContainer = document.getElementById('questions-container');
            data.questions.forEach(question => {
                const questionDiv = document.createElement('div');
                questionDiv.classList.add('question');
                questionDiv.innerHTML = `
                    <p>${question.question}</p>
                    <p>Type: ${question.type}</p>
                `;
                questionsContainer.appendChild(questionDiv);
            });
        })
        .catch(error => console.error('Error fetching questions:', error));
});


 // Recommendations 

document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("recommendationModal");
    const closeModal = modal ? modal.querySelector(".close") : null;
    const recommendationList = document.getElementById("modal-recommendations");
    const sourceElement = document.getElementById("modal-source");
    
    if (modal) modal.style.display = "none";

    if (closeModal) {
        closeModal.addEventListener("click", hideModal);
        window.addEventListener("click", (event) => {
            if (event.target === modal) hideModal();
        });
    } 

    async function fetchCommonStressors() {
        try {
            const response = await fetch("/recommendation/?format=json");
            if (response.ok) {
                const data = await response.json();
                updateStressorsInDOM(data.common_stressors);
            } else {
                console.warn("Failed to fetch common stressors. Status:", response.status);
            }
        } catch (error) {
            console.error("Error fetching common stressors:", error);
        }
    }

    function updateStressorsInDOM(stressors) {
        stressors.forEach(stressor => {
            const stressorElement = document.querySelector(`[data-stressor="${stressor.name}"]`);
            if (stressorElement) {
                stressorElement.setAttribute("data-severity", stressor.severity || 3);
                stressorElement.setAttribute("data-recommendations", JSON.stringify(stressor.recommendations));

                stressorElement.addEventListener("click", () => handleStressorClick(stressorElement));
            }
        });
       
    }

    async function handleStressorClick(stressorItem) {
        const stressorName = stressorItem.getAttribute('data-stressor');
        const severityLevel = parseInt(stressorItem.getAttribute('data-severity'), 10) || 3;

        try {
            const response = await fetch(`/get_recommendations/${stressorName}/${severityLevel}`);
            if (!response.ok) {
                console.warn(`Failed to fetch recommendations. Status: ${response.status}`);
                return;
            }

            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                displayModalData(stressorName, data.recommendations || []);
            } else {
                console.error("Expected JSON but received:", contentType);
            }
        } catch (error) {
            console.error("Error fetching recommendations:", error);
        }
    }

    function displayModalData(stressorName, recommendations) {
        const modalElement = document.getElementById("recommendationModal");
        const recommendationList = document.getElementById("modal-recommendations");
        const sourceElement = document.getElementById("modal-source");

        if (modalElement && recommendationList && sourceElement) {
            document.getElementById("modal-stressor-name").textContent = stressorName;
            recommendationList.innerHTML = '';

            if (recommendations && recommendations.length > 0) {
                recommendations.forEach(rec => {
                    const li = document.createElement('li');
                    li.textContent = rec.text;
                    recommendationList.appendChild(li);
                });
                sourceElement.textContent = `Source: ${recommendations[0].source || "Unknown"}`;
            } else {
                const noRecommendationItem = document.createElement('li');
                noRecommendationItem.textContent = "No recommendations available.";
                recommendationList.appendChild(noRecommendationItem);
                sourceElement.textContent = "";
            }

            modalElement.style.display = "flex";
        } 
    }

    function hideModal() {
        const modalElement = document.getElementById("recommendationModal");
        if (modalElement) modalElement.style.display = "none";
    }

    fetchCommonStressors();
});
