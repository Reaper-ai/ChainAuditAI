const API_BASE_URL = "http://localhost:8000"; // Backend URL

// Chart.js setup for traffic analysis
const ctx = document.getElementById('trafficChart').getContext('2d');

// Gradient for the Safe line
const gradientSafe = ctx.createLinearGradient(0, 0, 0, 400);
gradientSafe.addColorStop(0, 'rgba(59, 130, 246, 0.5)');
gradientSafe.addColorStop(1, 'rgba(59, 130, 246, 0)');

let trafficChart = null;
let dashboardData = {
    safeData: [],
    fraudData: [],
    labels: []
};

// Initialize chart
function initChart() {
    trafficChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dashboardData.labels,
            datasets: [
                {
                    label: 'Safe Transactions',
                    data: dashboardData.safeData,
                    borderColor: '#3b82f6',
                    backgroundColor: gradientSafe,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Fraud Attempts',
                    data: dashboardData.fraudData,
                    borderColor: '#ef4444',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

// Fetch dashboard data from backend
async function fetchDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/dash/`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        updateDashboard(data);
        
    } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        document.getElementById('feedHeading').innerText = `Live Block Feed - Error: ${error.message}`;
    }
}

// Update dashboard with real data
function updateDashboard(data) {
    const records = data.records || [];
    
    // Group by transaction type for chart
    const typeGroups = {
        vehicle: { safe: 0, fraud: 0 },
        bank: { safe: 0, fraud: 0 },
        ecommerce: { safe: 0, fraud: 0 },
        ethereum: { safe: 0, fraud: 0 }
    };
    
    records.forEach(record => {
        const type = record.transaction_type;
        if (typeGroups[type]) {
            if (record.fraud_score >= 50) {
                typeGroups[type].fraud++;
            } else {
                typeGroups[type].safe++;
            }
        }
    });
    
    // Update chart
    dashboardData.labels = ['Vehicle', 'Bank', 'E-Commerce', 'Ethereum'];
    dashboardData.safeData = [
        typeGroups.vehicle.safe,
        typeGroups.bank.safe,
        typeGroups.ecommerce.safe,
        typeGroups.ethereum.safe
    ];
    dashboardData.fraudData = [
        typeGroups.vehicle.fraud,
        typeGroups.bank.fraud,
        typeGroups.ecommerce.fraud,
        typeGroups.ethereum.fraud
    ];
    
    if (trafficChart) {
        trafficChart.data.labels = dashboardData.labels;
        trafficChart.data.datasets[0].data = dashboardData.safeData;
        trafficChart.data.datasets[1].data = dashboardData.fraudData;
        trafficChart.update();
    }
    
    // Update live feed
    updateLiveFeed(records);
}

// Update live feed with recent transactions
function updateLiveFeed(records) {
    const feedContainer = document.getElementById('liveFeed');
    feedContainer.innerHTML = ''; // Clear existing
    
    // Show most recent 10 records
    const recentRecords = records.slice(0, 10);
    
    if (recentRecords.length === 0) {
        feedContainer.innerHTML = `
            <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                No transactions yet. Use the scanner to test fraud detection.
            </div>
        `;
        return;
    }
    
    recentRecords.forEach(record => {
        const isFraud = record.fraud_score >= 50;
        const timeAgo = getTimeAgo(record.created_at);
        const txType = record.transaction_type.charAt(0).toUpperCase() + record.transaction_type.slice(1);
        
        const div = document.createElement('div');
        div.className = 'feed-item';
        div.innerHTML = `
            <div class="feed-header">
                <span>${txType}</span>
                <span>${timeAgo}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="feed-hash">DB ID: ${record.id} | Score: ${record.fraud_score}</span>
                <span style="
                    font-size: 0.7rem; 
                    font-weight: bold; 
                    padding: 2px 6px; 
                    border-radius: 4px; 
                    background: ${isFraud ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)'}; 
                    color: ${isFraud ? '#f87171' : '#4ade80'};
                ">
                    ${isFraud ? 'FRAUD' : 'SAFE'}
                </span>
            </div>
            ${record.blockchain_tx_hash ? `
                <div style="font-size: 0.7rem; color: var(--text-secondary); margin-top: 0.25rem;">
                    ⛓️ On-Chain: ${record.blockchain_tx_hash.substring(0, 20)}...
                </div>
            ` : ''}
        `;
        
        feedContainer.appendChild(div);
    });
}

// Helper function to calculate time ago
function getTimeAgo(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins === 1) return '1 min ago';
    if (diffMins < 60) return `${diffMins} mins ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return '1 hour ago';
    if (diffHours < 24) return `${diffHours} hours ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return '1 day ago';
    return `${diffDays} days ago`;
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log("Dashboard initialized. Backend:", API_BASE_URL);
    initChart();
    fetchDashboardData();
    
    // Auto-refresh every 5 seconds
    setInterval(fetchDashboardData, 5000);
});
