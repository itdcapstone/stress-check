 // Fetch the stressor data from the DOM (embedded in a hidden element)
 const stressorData = JSON.parse(document.getElementById("stressor-data").textContent);

 // Sort the data by percentage in descending order
 const sortedData = stressorData.sort((a, b) => b.percentage - a.percentage);

 // Extract sorted labels, percentages, and student counts
 const labels = sortedData.map(item => item.stressor);
 const percentages = sortedData.map(item => item.percentage);
 const studentCounts = sortedData.map(item => item.student_count);

 // Get the chart context
 const ctx = document.getElementById('stressorBarChart').getContext('2d');

 // Create the Chart.js bar chart
 new Chart(ctx, {
     type: 'bar',
     data: {
         labels: labels,
         datasets: [{
             label: 'Stressor Percentage',
             data: percentages,
             backgroundColor: 'rgba(75, 192, 192, 0.6)',
             borderColor: 'rgba(75, 192, 192, 1)',
             borderWidth: 1
         }]
     },
     options: {
         responsive: true,
         maintainAspectRatio: false, // Allow the chart to fill the container
         scales: {
             y: {
                 beginAtZero: true,
                 max: 10, // Adjust the maximum value for the chart
                 title: { display: true, text: 'Percentage (%)' }
             },
             x: {
                 title: { display: true, text: 'Stressors' }
             }
         },
         plugins: {
             legend: { display: false },
             tooltip: {
                 callbacks: {
                     label: (context) => {
                         const percentage = context.raw;
                         const count = studentCounts[context.dataIndex];
                         return `${context.label}: ${percentage.toFixed(2)}% (${count} assessments)`;
                     }
                 }
             }
         }
     }
 });


google.charts.load('current', { 'packages': ['corechart'] });
google.charts.setOnLoadCallback(drawPieChart);

function drawPieChart() {
    // Data passed from Flask to JavaScript
    const stressLevelData = JSON.parse(document.getElementById('stress-level-data').textContent);

    // Transform data to format required by Google Charts
    const chartData = [['Stress Level', 'Number of Students']];
    stressLevelData.forEach(item => {
        chartData.push([`Level ${item.stress_level}`, item.count]);
    });

    // Convert array to Google Charts DataTable
    const data = google.visualization.arrayToDataTable(chartData);

    // Chart options
    const options = {
        chartArea: { width: '100%', height: '80%' },
        backgroundColor: 'transparent',
        colors: ['#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6'],
        legend: { position: 'bottom', textStyle: { color: '#333', fontSize: 14 } }
    };

    // Draw chart
    const chart = new google.visualization.PieChart(document.getElementById('piechart'));
    chart.draw(data, options);

    // Handle resizing
    window.addEventListener('resize', () => chart.draw(data, options));
}


// Toast Notification Logic
window.onload = function () {
    const successMessage = sessionStorage.getItem('success_message');
    if (successMessage) {
        showToast(successMessage, 'success');
        sessionStorage.removeItem('success_message');
    }
};

function showToast(message, type) {
    const toast = document.getElementById('toast');
    if (!toast) {
        console.error('Toast element not found!');
        return;
    }
    toast.innerText = message;
    toast.classList.remove('show', 'success', 'error', 'fade-out');
    toast.classList.add('show', type);
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.classList.remove('show', 'fade-out');
            toast.innerText = '';
        }, 500);
    }, 3000);
}
