document.addEventListener('DOMContentLoaded', function () {
    const saveChangesBtn = document.getElementById('saveChangesBtn');
    
    if (saveChangesBtn) {
      console.log('Save Changes button found');
      
      saveChangesBtn.addEventListener('click', function (event) {
        event.preventDefault(); // Prevent default action (if necessary)
        console.log('Save Changes button clicked');
        
        // Get the form data
        const faqId = document.getElementById('editFaqId').value;
        const question = document.getElementById('editFaqQuestion').value;
        const answer = document.getElementById('editFaqAnswer').value;
        
        // Log the form data to verify it
        console.log(`FAQ ID: ${faqId}, Question: ${question}, Answer: ${answer}`);
      
        // Send the AJAX request to update the FAQ
        fetch('/admin/faqs_management/edit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: `faq_id=${faqId}&question=${encodeURIComponent(question)}&answer=${encodeURIComponent(answer)}`
        })
          .then(response => response.json())
          .then(data => {
            console.log('Response from server:', data);
            if (data.success) {
              console.log('FAQ updated successfully');
              
              // Store a flag in localStorage to indicate that the FAQ was updated
              localStorage.setItem('faqUpdated', 'true');
              
              // Reload the page
              window.location.reload();
            } else {
              console.error('Error in response:', data.message);
            }
          })
          .catch(error => console.error('Error updating FAQ:', error));
      });
    } else {
      console.error('Save Changes button not found');
    }
  
    // Check if the FAQ was updated after the page reloads
    if (localStorage.getItem('faqUpdated') === 'true') {
      showToast('FAQ updated successfully!');
      // Clear the flag from localStorage after the toast is shown
      localStorage.removeItem('faqUpdated');
    }
  });
  
  

  document.addEventListener('DOMContentLoaded', function () {
    // Use event delegation for the Delete button in the modal
    document.body.addEventListener('click', function (event) {
      // Check if the clicked element is the delete button
      if (event.target && event.target.id === 'deleteFaqBtn') {
        event.preventDefault(); // Prevent the default button behavior
  
        // Get the FAQ ID from the modal input field
        const faqId = document.getElementById('deleteFaqId').value;
        console.log('Delete button clicked. FAQ ID:', faqId);
  
        // Send an AJAX request to delete the FAQ
        fetch('/admin/faqs_management/delete', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: `faq_id=${faqId}`
        })
          .then(response => response.json())
          .then(data => {
            console.log('Response from server:', data);
            if (data.success) {
              console.log('FAQ deleted successfully');
              // Optionally, close the modal and refresh the page
              window.location.reload();
            } else {
              console.error('Error in response:', data.message);
            }
          })
          .catch(error => console.error('Error deleting FAQ:', error));
      }
    });
  });


  function showToast(message) {
    // Get the toast container
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    
    // Set the toast message
    toastMessage.textContent = message;
  
    // Add the 'show' class to display the toast
    toast.classList.add('show');
  
    // Automatically hide the toast after 3 seconds
    setTimeout(function () {
      toast.classList.remove('show');
    }, 3000);
  }