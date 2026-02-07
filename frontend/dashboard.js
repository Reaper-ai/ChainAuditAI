const ctx = document.getElementById('trafficChart').getContext('2d');

// Gradient for the Safe line
const gradientSafe = ctx.createLinearGradient(0, 0, 0, 400);
gradientSafe.addColorStop(0, 'rgba(59, 130, 246, 0.5)');
gradientSafe.addColorStop(1, 'rgba(59, 130, 246, 0)');

const safeDataPoints = [1200, 1900, 3000, 5000, 4200, 6000, 8245, 9100, 10400, 11800, 13200, 15000, 16800, 18900, 21000];
const fraudDataPoints = [50, 80, 120, 200, 150, 180, 1402, 1600, 1750, 1900, 2100, 2300, 2500, 2800, 3000];
const labels = safeDataPoints.map((_, i) => `T${i + 1}`);

const trafficChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: labels,
        datasets: [
            {
                label: 'Safe Transactions',
                data: safeDataPoints,
                borderColor: '#3b82f6',
                backgroundColor: gradientSafe,
                fill: true,
                tension: 0.4
            },
            {
                label: 'Fraud Attempts',
                data: fraudDataPoints,
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

function refreshData() {
    const totalTx = document.getElementById('totalTx');
    const valSecured = document.getElementById('valSecured');
    
    // Randomised values for demo purposes
    let currentTx = parseInt(totalTx.innerText.replace(/,/g, ''));
    totalTx.innerText = (currentTx + Math.floor(Math.random() * 50)).toLocaleString();
    
    // Animation effect
    totalTx.style.color = "#3b82f6";
    setTimeout(() => totalTx.style.color = "var(--text-primary)", 500);
}

// Auto-refresh every 5 seconds
setInterval(refreshData, 5000);

//Feed Simulation
const feedContainer = document.getElementById('liveFeed');

function addFeedItem() {
    const isFraud = Math.random() > 0.8;
    const hash = "0x" + Math.random().toString(16).slice(2, 6) + "...";
    const region = ["US-East", "EU-West", "Asia-Pac", "SA-East"][Math.floor(Math.random() * 4)];
    
    const div = document.createElement('div');
    div.className = 'feed-item';
    div.innerHTML = `
        <div class="feed-header">
            <span>${region}</span>
            <span>Just now</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="feed-hash">${hash}</span>
            <span style="
                font-size: 0.7rem; 
                font-weight: bold; 
                padding: 2px 6px; 
                border-radius: 4px; 
                background: ${isFraud ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)'}; 
                color: ${isFraud ? '#f87171' : '#4ade80'};
            ">
                ${isFraud ? 'BLOCKED' : 'VERIFIED'}
            </span>
        </div>
    `;
    
    // Add to top
    feedContainer.prepend(div);
    
    // Keep list short (max 10 items)
    if (feedContainer.children.length > 10) {
        feedContainer.lastElementChild.remove();
    }
}

// Add a new feed item every 2.5 seconds
setInterval(addFeedItem, 2500);

// Initial items 
addFeedItem();
addFeedItem();
addFeedItem();