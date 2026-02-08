// ===============================
// CONFIG
// ===============================
// Ensure this matches your backend URL (no trailing slash)
const API_BASE_URL = "http://localhost:8000"; 

// Chart.js setup
const ctx = document.getElementById('trafficChart').getContext('2d');
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
    if (trafficChart) return; // Prevent double init
    
    trafficChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Vehicle', 'Bank', 'E-Com', 'Ethereum'],
            datasets: [
                {
                    label: 'Safe',
                    data: [0, 0, 0, 0],
                    borderColor: '#3b82f6',
                    backgroundColor: gradientSafe,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Fraud',
                    data: [0, 0, 0, 0],
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
            plugins: { legend: { display: true, labels: { color: '#94a3b8' } } },
            scales: {
                y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            }
        }
    });
}

// Fetch Data
async function fetchDashboardData() {
    try {
        // FIX: Point to the specific /stats endpoint
        const response = await fetch(`${API_BASE_URL}/stats/`);
        
        // FIX: Check if response is actually JSON before parsing
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 50)}...`);
        }

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        
        const data = await response.json();
        updateDashboard(data);
        
    } catch (error) {
        console.error("Dashboard Error:", error);
        const feed = document.getElementById('liveFeed');
        if(feed) feed.innerHTML = `<div style="color:red; padding:20px;">Connection Error: ${error.message}. Is Backend running?</div>`;
    }
}

// Update UI
function updateDashboard(data) {
    const records = data.records || [];
    
    // 1. Calculate Stats
    const stats = {
        vehicle: { safe: 0, fraud: 0 },
        bank: { safe: 0, fraud: 0 },
        ecommerce: { safe: 0, fraud: 0 },
        ethereum: { safe: 0, fraud: 0 }
    };
    
    records.forEach(r => {
        const type = r.transaction_type;
        if (stats[type]) {
            if (r.fraud_score > 50) stats[type].fraud++;
            else stats[type].safe++;
        }
    });

    // 2. Update Header Cards
    document.getElementById('total-scans').innerText = records.length;
    const totalFraud = Object.values(stats).reduce((acc, curr) => acc + curr.fraud, 0);
    document.getElementById('fraud-detected').innerText = totalFraud;
    
    // 3. Update Chart
    if (trafficChart) {
        trafficChart.data.datasets[0].data = [
            stats.vehicle.safe, stats.bank.safe, stats.ecommerce.safe, stats.ethereum.safe
        ];
        trafficChart.data.datasets[1].data = [
            stats.vehicle.fraud, stats.bank.fraud, stats.ecommerce.fraud, stats.ethereum.fraud
        ];
        trafficChart.update();
    }
    
    updateLiveFeed(records);
}

// Update Live Feed
function updateLiveFeed(records) {
    const feed = document.getElementById('liveFeed');
    feed.innerHTML = '';
    
    // Show top 10 recent
    records.slice(0, 10).forEach(record => {
        const isFraud = record.fraud_score > 50;
        const hashDisplay = record.tx_hash ? `${record.tx_hash.substring(0, 10)}...` : 'Pending';
        
        // Check if we have real blockchain data fetched
        const chainInfo = record.blockchain_data 
            ? `<span style="color:#4ade80; font-size:0.7em;">✓ On-Chain Block: ${record.blockchain_data.timestamp}</span>`
            : '';

        const item = document.createElement('div');
        item.className = 'feed-item';
        item.innerHTML = `
            <div class="feed-header">
                <span style="text-transform: capitalize;">${record.transaction_type}</span>
                <span style="font-size:0.8em; color:#64748b;">${new Date(record.created_at).toLocaleTimeString()}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:5px;">
                <div style="display:flex; flex-direction:column;">
                    <span class="feed-hash">TX: ${hashDisplay}</span>
                    ${chainInfo}
                </div>
                <span style="
                    background: ${isFraud ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)'};
                    color: ${isFraud ? '#f87171' : '#4ade80'};
                    padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;
                ">
                    ${record.fraud_score} / 100
                </span>
            </div>
        `;
        feed.appendChild(item);
    });
}

// Start
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchDashboardData();
    setInterval(fetchDashboardData, 3000); // Poll every 3 seconds
});