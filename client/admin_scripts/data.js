google.charts.load('current', { packages: ['corechart', 'bar'] });
google.charts.setOnLoadCallback(drawColumnChart);

let columnChart;

function drawColumnChart() {
    const data = google.visualization.arrayToDataTable(columnChartData);

    const options = {
        title: 'Average Stress Level by Year Level',
        backgroundColor: 'transparent',
        hAxis: { title: 'Year Level' },
        vAxis: { title: 'Average Stress Level', minValue: 0 },
        legend: { position: 'none' },
        colors: ['#4285F4'],
        chartArea: {
            left: '10%',
            top: '10%',
            width: '80%',
            height: '70%',
            backgroundColor: 'transparent',
        },
    };

    const chartContainer = document.getElementById('column_chart_div');
    columnChart = new google.visualization.ColumnChart(chartContainer);
    columnChart.draw(data, options);
}

window.addEventListener('resize', () => {
    if (columnChart) drawColumnChart();
});

google.charts.load('current', { packages: ['corechart', 'line'] });
google.charts.setOnLoadCallback(drawLineChart);

let lineChart;

function drawLineChart() {
    const data = google.visualization.arrayToDataTable(lineChartData);

    const options = {
        title: 'Average Stress Levels Over Time',
        backgroundColor: 'transparent',
        hAxis: { title: 'Month', titleTextStyle: { color: '#333' } },
        vAxis: { title: 'Average Stress Level', minValue: 0 },
        curveType: 'function',
        legend: { position: 'bottom' },
        chartArea: { left: '10%', top: '10%', width: '80%', height: '65%' },
    };

    const chartContainer = document.getElementById('chart_div');
    lineChart = new google.visualization.LineChart(chartContainer);
    lineChart.draw(data, options);
}

window.addEventListener('resize', () => {
    if (lineChart) drawLineChart();
});

google.charts.load('current', { packages: ['corechart'] });
google.charts.setOnLoadCallback(drawPieChart);

function drawPieChart() {
    const chartData = [['Stress Level', 'Number of Students']].concat(
        stressLevelData.map(item => [`Level ${item.stress_level}`, item.count])
    );

    const data = google.visualization.arrayToDataTable(chartData);

    const options = {
        chartArea: { width: '100%', height: '80%' },
        backgroundColor: 'transparent',
        colors: ['#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6'],
        legend: { position: 'bottom', textStyle: { color: '#333', fontSize: 14 } },
    };

    const chart = new google.visualization.PieChart(document.getElementById('piechart'));
    chart.draw(data, options);

    window.addEventListener('resize', drawPieChart);
}

const labels = stressorData.map(item => item.stressor);
const percentages = stressorData.map(item => item.percentage);
const studentCounts = stressorData.map(item => item.student_count);

const ctx = document.getElementById('stressorBarChart').getContext('2d');

const stressorBarChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: labels,
        datasets: [{
            label: 'Stressor Percentage',
            data: percentages,
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: true, max: 10, title: { display: true, text: 'Percentage (%)' } },
            x: { title: { display: true, text: 'Stressors' } },
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: context => {
                        const percentage = context.raw;
                        const count = studentCounts[context.dataIndex];
                        return `${context.label}: ${percentage.toFixed(2)}% (${count} assessments)`;
                    }
                }
            }
        }
    }
});

window.addEventListener('resize', () => stressorBarChart.resize());
