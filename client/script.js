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

document.addEventListener('DOMContentLoaded', function () {
    const editLink = document.getElementById('edit-profile-link');
    const formButtons = document.getElementById('formButtons');
    const cancelButton = document.getElementById('cancel-button');
    const submitButton = document.getElementById('submit-button');
    const formFields = document.querySelectorAll('.profile-container input, .profile-container select');

    const cancelModal = document.getElementById('cancel-modal');
    const closeCancelModal = document.getElementById('close-cancel-modal');
    const confirmCancel = document.getElementById('confirm-cancel');
    const cancelModalButton = document.getElementById('cancel-modal-button');

    // Store original form values
    let originalFormData = {};

    // Function to save current form data
    const saveOriginalFormData = () => {
        originalFormData = {};
        formFields.forEach(field => {
            originalFormData[field.name] = field.value;
        });
    };

    // Function to restore original form data
    const restoreOriginalFormData = () => {
        formFields.forEach(field => {
            if (originalFormData[field.name] !== undefined) {
                field.value = originalFormData[field.name];
            }
        });
    };

    // Enable edit mode
    editLink.addEventListener('click', (e) => {
        e.preventDefault();
        formButtons.style.display = 'block';
        formFields.forEach(field => field.disabled = false);
        saveOriginalFormData(); // Save the original data when edit mode is enabled
    });

    // Open cancel modal
    cancelButton.addEventListener('click', () => {
        cancelModal.style.display = 'block';
    });

    // Confirm cancel action
    confirmCancel.addEventListener('click', () => {
        cancelModal.style.display = 'none';
        formButtons.style.display = 'none';
        restoreOriginalFormData(); // Restore original data on cancel
        formFields.forEach(field => field.disabled = true);
    });

    // Close cancel modal and continue editing
    cancelModalButton.addEventListener('click', () => {
        cancelModal.style.display = 'none';
    });

    // Close modal by clicking the close button
    closeCancelModal.addEventListener('click', () => {
        cancelModal.style.display = 'none';
    });

    // Close modal if clicking outside
    window.onclick = (event) => {
        if (event.target === cancelModal) {
            cancelModal.style.display = 'none';
        }
    };
});


document.addEventListener('DOMContentLoaded', function () {
    const changeEmailModal = document.getElementById('change-email-modal');
    const changeEmailButton = document.querySelector('.change-email');
    const closeChangeEmailModal = document.getElementById('close-change-email-modal');
    const passwordField = document.getElementById('email-password');
    const inputGroup = document.querySelector('.input-group'); // Target the input group container

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
        let existingErrorMessage = document.getElementById('password-error-message');
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
                // Create the error message
                const errorMessageDiv = document.createElement('div');
                errorMessageDiv.id = 'password-error-message';
                errorMessageDiv.textContent = "Incorrect password. Please try again.";
                errorMessageDiv.style.color = 'red'; // Make the text red
                errorMessageDiv.style.fontSize = '0.9em'; // Slightly smaller font
                errorMessageDiv.style.marginTop = '5px'; // Add space between the input group and message

                // Append the error message below the input group
                inputGroup.parentNode.insertBefore(errorMessageDiv, inputGroup.nextSibling);

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



document.addEventListener('DOMContentLoaded', function () {
    const changePasswordModal = document.getElementById('change-password-modal');
    const changePasswordButton = document.querySelector('.change-password');
    const closeChangePasswordModal = document.getElementById('close-change-password-modal');

    if (!changePasswordModal || !changePasswordButton || !closeChangePasswordModal) {
        console.error('Required elements not found in the DOM!');
        return;
    }

    // Show the modal when the button is clicked
    changePasswordButton.addEventListener('click', function () {
        console.log('Change Password button clicked!');
        changePasswordModal.style.display = 'block';
    });

    // Close the modal when the close button is clicked
    closeChangePasswordModal.addEventListener('click', function () {
        console.log('Close button clicked!');
        changePasswordModal.style.display = 'none';
    });

    // Close the modal if the user clicks outside it
    window.addEventListener('click', function (event) {
        if (event.target === changePasswordModal) {
            console.log('Clicked outside modal!');
            changePasswordModal.style.display = 'none';
        }
    });

    // Password form submission handling
    const changePasswordForm = document.getElementById('change-password-form');
    const currentPasswordField = document.getElementById('current-password');
    const newPasswordField = document.getElementById('new-password');
    const confirmNewPasswordField = document.getElementById('confirm-new-password');
    const currentPasswordError = document.getElementById('current-password-error');

    // Add focusout event for confirm password validation
    confirmNewPasswordField.addEventListener('focusout', function () {
        if (newPasswordField.value.trim() !== confirmNewPasswordField.value.trim()) {
            confirmNewPasswordField.setCustomValidity("Passwords do not match.");
        } else {
            confirmNewPasswordField.setCustomValidity("");
        }
        confirmNewPasswordField.reportValidity();
    });

    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', function (e) {
            e.preventDefault();

            if (!currentPasswordField || !newPasswordField || !confirmNewPasswordField || !currentPasswordError) {
                console.error('Password fields or error elements not found!');
                return;
            }

            currentPasswordError.style.display = 'none';

            const currentPassword = currentPasswordField.value.trim(); // Trim any extra spaces
            const newPassword = newPasswordField.value.trim(); // Trim any extra spaces
            const confirmNewPassword = confirmNewPasswordField.value.trim(); // Trim any extra spaces

            console.log('New Password:', newPassword); // Debugging output
            console.log('Confirm New Password:', confirmNewPassword); // Debugging output

            // Compare trimmed values during form submission
            if (newPassword !== confirmNewPassword) {
                console.log('Passwords do not match!'); // Debugging output
                confirmNewPasswordField.setCustomValidity("Passwords do not match.");
                confirmNewPasswordField.reportValidity();
                return;
            } else {
                confirmNewPasswordField.setCustomValidity("");
            }

            // Check the current password
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
    }
});



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
                console.warn("Failed to fetch Contributing Stressors. Status:", response.status);
            }
        } catch (error) {
            console.error("Error fetching Contributing Stressors:", error);
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
