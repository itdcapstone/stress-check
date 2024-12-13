function showCategoriesModal() {
    document.getElementById('categoriesModal').style.display = 'flex';
}

function closeCategoriesModal() {
    document.getElementById('categoriesModal').style.display = 'none';
}

// Close the modal if the user clicks outside of it
window.onclick = function(event) {
    const modal = document.getElementById('categoriesModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('myModal');
    
    // Ensure modal is hidden on load
    modal.style.display = 'none';

    // Example: Show modal only on button click
    document.getElementById('showModalBtn').addEventListener('click', () => {
        modal.style.display = 'block';
    });

    // Example: Close modal when close button is clicked
    document.querySelector('.close').addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Example: Close modal when clicking outside of it
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
});

function toggleDescription(button) {
    // Find the <li> that the button belongs to
    var listItem = button.closest('li');
    // Toggle the 'expanded' class on the <li>
    listItem.classList.toggle('expanded');
    // Change the button text based on expansion state
    if (listItem.classList.contains('expanded')) {
        button.textContent = 'Read less';
    } else {
        button.textContent = 'Read more';
    }
}


function showModal(username, age, yearLevel, date, stressLevel, stressors) {
    document.getElementById('modalUsername').textContent = username;
    document.getElementById('modalAge').textContent = age;
    document.getElementById('modalYearLevel').textContent = yearLevel;
    document.getElementById('modalDate').textContent = date;
    document.getElementById('modalStressLevel').textContent = stressLevel;
    document.getElementById('modalStressors').textContent = stressors;

    document.getElementById('assessmentModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('assessmentModal').style.display = 'none';
}

// Close the modal if clicked outside
window.onclick = function(event) {
    const modal = document.getElementById('assessmentModal');
    if (event.target === modal) {
        closeModal();
    }
}


document.addEventListener('DOMContentLoaded', function () {
    // Data for the bar chart (from backend)
    const stressorData = {{ stressor_data|tojson }};
    
    // Prepare data for the chart
    const labels = stressorData.map(item => item.stressor);
    const data = stressorData.map(item => item.percentage);
    const tooltipData = stressorData.map(item => `${item.student_count} students`);

    // Create the bar chart
    const ctx = document.getElementById('stressorBarChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Percentage',
                data: data,
                backgroundColor: '#4285F4',
                borderColor: '#3367D6',
                borderWidth: 1,
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.raw.toFixed(2)}% (${tooltipData[context.dataIndex]})`;
                        }
                    }
                }
            },
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Percentage (%)' }
                },
                x: {
                    title: { display: true, text: 'Stressors' }
                }
            }
        }
    });
});