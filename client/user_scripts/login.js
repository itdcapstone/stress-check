function showModal(modalId) {
    document.getElementById(modalId).classList.add('show');
  }
  
  function hideModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
    if (modalId === 'incorrectLoginModal') {
      // Clear the password input field
      document.querySelector('input[name="password"]').value = '';
    }
  }

  // Trigger modal based on the login response
  const incorrectLogin = '{{ incorrect_login|default(False) }}'; // Passed from backend
  const userNotFound = '{{ user_not_found|default(False) }}'; // Passed from backend

  if (incorrectLogin === 'True') {
    showModal('incorrectLoginModal');
  } else if (userNotFound === 'True') {
    showModal('userNotFoundModal');
  }

  function togglePasswordVisibility() {
      const passwordInput = document.getElementById('password');
      const toggleIcon = document.getElementById('togglePassword');
      
      if (passwordInput.type === 'password') {
          passwordInput.type = 'text'; // Show password
          toggleIcon.classList.remove('bxs-show'); // Change to hide icon
          toggleIcon.classList.add('bxs-hide'); // Assuming you have a 'bxs-hide' icon
      } else {
          passwordInput.type = 'password'; // Hide password
          toggleIcon.classList.remove('bxs-hide'); // Change back to show icon
          toggleIcon.classList.add('bxs-show');
      }
  }