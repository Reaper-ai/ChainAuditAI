const API_BASE_URL = "http://localhost:8000"; 

const ctx = document.getElementById('trafficChart').getContext('2d');

// Bins for AI Risk Scores (0 to 100)
const scoreLabels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100'];

// Initialize with empty data (will be filled by fetch)
let trafficChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: scoreLabels,
        datasets: [
            {
                label: 'Transaction Frequency',
                data: [], // Starts empty
                backgroundColor: [], // Dynamic colors set on update
                borderRadius: 4,
                borderSkipped: false,
                barPercentage: 0.7,
                categoryPercentage: 0.8
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false }, // Hide legend
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `Volume: ${context.raw} txns`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: '#334155' },
                ticks: { color: '#94a3b8' },
                title: {
                    display: true,
                    text: 'Frequency (Tx Count)',
                    color: '#64748b',
                    font: { size: 10 }
                }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#94a3b8' },
                title: {
                    display: true,
                    text: 'AI Risk Score Range',
                    color: '#64748b',
                    font: { size: 10 }
                }
            }
        },
        animation: {
            duration: 1500,
            easing: 'easeOutQuart'
        }
    }
});

async function fetchDashboardData() {
    try {
        // FIX: Point to the specific /stats endpoint
        const response = await fetch(`${API_BASE_URL}/stats/`);
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        const records = data.records || [];

        updateMetrics(records);

        updateChartData(records);

        updateLiveFeed(records);
        
    } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
    }
}

function updateChartData(records) {
    // Initialize 10 bins with 0
    const bins = Array(10).fill(0);

    records.forEach(record => {
        // Ensure score is within 0-100
        const score = Math.max(0, Math.min(record.fraud_score, 100));
        
        // Calculate index: Score 85 -> index 8. Score 100 -> index 9.
        const binIndex = score === 100 ? 9 : Math.floor(score / 10);
        bins[binIndex]++;
    });

    // Dynamic Coloring Logic: Safe (0-80) = Blue, High Risk (81-100) = Red
    const backgroundColors = bins.map((_, index) => {
        // Bins 0-7 (Scores 0-80) are Blue
        // Bins 8-9 (Scores 81-100) are Red
        return index >= 8 ? '#ef4444' : '#3b82f6';
    });

    // Update Chart Instance
    trafficChart.data.datasets[0].data = bins;
    trafficChart.data.datasets[0].backgroundColor = backgroundColors;
    trafficChart.update();
}


function updateLiveFeed(records) {
    const feedContainer = document.getElementById('liveFeed');
    if(!feedContainer) return;

    feedContainer.innerHTML = ''; // Clear existing
    
    // Sort by newest first (using created_at timestamp) and take top 10
    const sortedRecords = [...records].sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
    ).slice(0, 10);
    
    if (sortedRecords.length === 0) {
        feedContainer.innerHTML = `<div style="text-align:center; padding:1rem; color:#64748b;">No activity yet.</div>`;
        return;
    }

    sortedRecords.forEach(record => {
        const isFraud = record.fraud_score > 50;
        const timeAgo = getTimeAgo(record.created_at);
        const type = record.transaction_type || "Unknown";

        // Create feed item
        const div = document.createElement('div');
        div.className = 'feed-item';
        div.innerHTML = `
            <div class="feed-header">
                <span style="text-transform: capitalize;">${type}</span>
                <span>${timeAgo}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="feed-hash">ID: ${record.id}</span>
                <span style="
                    background: ${isFraud ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)'};
                    color: ${isFraud ? '#f87171' : '#4ade80'};
                    padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;
                ">
                    ${isFraud ? 'BLOCKED' : 'VERIFIED'} (Score: ${record.fraud_score})
                </span>
            </div>
        `;
        feedContainer.appendChild(div);
    });
}

// Calculate "Time Ago"
function getTimeAgo(dateString) {
    if(!dateString) return '';
    const date = new Date(dateString);
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + "y ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + "mo ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + "d ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + "h ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + "m ago";
    return Math.floor(seconds) + "s ago";
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    console.log("Dashboard initialized. Connecting to:", API_BASE_URL);
    fetchDashboardData();
    
    // Auto-refresh every 5 seconds
    setInterval(fetchDashboardData, 5000);
});