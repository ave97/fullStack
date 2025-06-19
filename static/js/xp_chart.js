document.addEventListener("DOMContentLoaded", () => {
    if (!chartData || !Array.isArray(chartData) || chartData.length === 0) {
        console.warn("No chart data to display.");
        return;
    }

    const ctx = document.getElementById("xpChart").getContext("2d");

    const labels = chartData.map(item => item.label);
    const data = chartData.map(item => item.value);

    // Δυναμικά χρώματα
    const colors = chartData.map(item => {
        if (item.value >= 90) return "#06d6a0";      // Πράσινο
        if (item.value >= 60) return "#ffd166";      // Πορτοκαλί
        return "#ef476f";                            // Κόκκινο
    });

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Success Rate (%)",
                data: data,
                backgroundColor: colors,
                borderRadius: 10,
                hoverBackgroundColor: "#118ab2",
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            animation: {
                duration: 900,
                easing: "easeOutCubic"
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        callback: value => value + "%"
                    },
                    title: {
                        display: true,
                        text: "Success Rate (%)",
                        font: { size: 14, weight: 'bold' },
                        color: "#333"
                    },
                    grid: {
                        color: "#e0e0e0"
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: "Lesson",
                        font: { size: 14, weight: 'bold' },
                        color: "#333"
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0
                    },
                    grid: {
                        display: false
                    },
                    categoryPercentage: 0.6,
                    barPercentage: 0.7
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const index = context.dataIndex;
                            const item = chartData[index];
                            return `${item.correct}/${item.total} correct (${item.value}%)`;
                        }
                    }
                }
            }
        }
    });
});
