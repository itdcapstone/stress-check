document.addEventListener('DOMContentLoaded', function() {
    var addUserLink = document.querySelector('.btn-add-user'); // Button to open the form
    var addUserForm = document.getElementById('addUserForm'); // Form element

    // Ensure the elements exist
    if (addUserLink && addUserForm) {
        addUserLink.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent the default link behavior

            // Toggle the form visibility
            if (addUserForm.style.display === 'none' || addUserForm.style.display === '') {
                addUserForm.style.display = 'block'; // Show the form
            } else {
                addUserForm.style.display = 'none'; // Hide the form
            }
        });
    }
});

document.getElementById("filterForm").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent the form from submitting normally

    // Get the date value from the form
    const dateFilter = document.getElementById("dateFilter").value;

    // Send an AJAX request to the server with the dateFilter
    fetch(`/admin/feedback/?dateFilter=${dateFilter}`, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
    .then(response => response.json())
    .then(data => {
        // Update the table with filtered feedback data
        const tableBody = document.querySelector(".feedback-table tbody");
        tableBody.innerHTML = ""; // Clear current table data

        data.feedback_data.forEach(feedback => {
            // Create a new row for each feedback item
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${feedback.username}</td>
                <td>${feedback.feedback}</td>
                <td>${feedback.timestamp}</td>
                <td>
                    <button class="btn-icon view-feedback" title="View">
                        <i class='bx bx-show'></i>
                    </button>
                    <button class="btn-icon delete-feedback" title="Delete">
                        <i class='bx bx-trash'></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    })
    .catch(error => console.error("Error fetching filtered data:", error));
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





