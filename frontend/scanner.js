// ===============================
// CONFIG
// ===============================
const API_BASE_URL = "http://localhost:5000/api";


// ===============================
// GLOBAL STATE
// ===============================
let state = {
    currentTransactionType: "vehicle", // default dataset
    currentModel: "lightgbm",
    currentSignal: null,               // 'fraud' or 'legit'
    lastResult: null
};


// ===============================
// MODEL SELECTION
// ===============================
function selectModel(card, modelId) {
    document.querySelectorAll(".model-card")
        .forEach(c => c.classList.remove("active"));

    card.classList.add("active");
    state.currentModel = modelId;

    console.log("[State] Model:", modelId);
}


// ===============================
// SIGNAL SELECTION
// ===============================
function selectSignal(card, signalType) {
    document.querySelectorAll(".signal-card")
        .forEach(c => c.classList.remove("active"));

    card.classList.add("active");
    state.currentSignal = signalType;

    console.log("[State] Signal:", signalType);
}


// ===============================
// RUN ANALYSIS
// ===============================
async function runAnalysis() {
    const analyzeBtn = document.getElementById("analyzeBtn");
    const resultCard = document.getElementById("resultCard");
    const placeholder = document.getElementById("placeholder");

    if (!state.currentSignal) {
        alert("Please select Fraud or Legit signal.");
        return;
    }

    // Payload sent to backend
    const payload = {
        transaction_type: state.currentTransactionType,
        model_used: state.currentModel,
        forced_signal: state.currentSignal,
        fraud_label: state.currentSignal === "fraud" ? "fraud" : "non-fraud",
        timestamp: new Date().toISOString()
    };

    // UI Loading State
    analyzeBtn.innerText = "Broadcasting...";
    analyzeBtn.disabled = true;
    analyzeBtn.style.opacity = "0.7";

    resultCard.classList.add("hidden");
    placeholder.classList.remove("hidden");

    placeholder.innerHTML = `
        <div style="display:flex; flex-direction:column; align-items:center; gap:10px;">
            <div class="spinner"></div>
            Sending <strong>${state.currentSignal.toUpperCase()}</strong> signal  
            via <strong>${state.currentModel}</strong>  
            (${state.currentTransactionType})
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(response.statusText);
        }

        const data = await response.json();
        state.lastResult = data;

        renderResults(data);

    } catch (error) {
        console.error("Analysis Error:", error);
        placeholder.innerHTML = "Error connecting to backend.";
        alert("Backend connection failed.");
    } finally {
        analyzeBtn.innerText = "Broadcast Signal";
        analyzeBtn.disabled = false;
        analyzeBtn.style.opacity = "1";
    }
}


// ===============================
// RENDER RESULTS
// ===============================
function renderResults(data) {
    const placeholder = document.getElementById("placeholder");
    const resultCard = document.getElementById("resultCard");

    const riskBadge = document.getElementById("riskBadge");
    const scoreValue = document.getElementById("scoreValue");
    const scoreText = document.getElementById("scoreText");
    const proofHash = document.getElementById("proofHash");
    const commitBtn = document.getElementById("commitBtn");

    placeholder.classList.add("hidden");
    resultCard.classList.remove("hidden");

    resultCard.classList.remove("high-risk", "low-risk");

    // Risk styling
    if (data.risk_level === "HIGH" || state.currentSignal === "fraud") {
        resultCard.classList.add("high-risk");
        riskBadge.innerText = "FRAUD DETECTED";
        riskBadge.style.background = "#ef4444";
        scoreValue.style.color = "#fca5a5";
    } else {
        resultCard.classList.add("low-risk");
        riskBadge.innerText = "LEGITIMATE";
        riskBadge.style.background = "#22c55e";
        scoreValue.style.color = "#86efac";
    }

    // Backend data
    scoreValue.innerText = data.score || "--";
    scoreText.innerText = data.message || "Analysis complete.";
    proofHash.innerText = data.proof_hash || "No hash returned";

    // Enable commit
    commitBtn.disabled = false;
    commitBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        Commit Proof to Chain
    `;
    commitBtn.style.background = "#334155";
}


// ===============================
// COMMIT TO LEDGER
// ===============================
async function commitToLedger() {
    const commitBtn = document.getElementById("commitBtn");

    if (!state.lastResult) {
        alert("No analysis data to commit.");
        return;
    }

    commitBtn.innerText = "Committing...";
    commitBtn.disabled = true;
    commitBtn.style.background = "#4f46e5";

    try {
        const response = await fetch(`${API_BASE_URL}/commit`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                proof_hash: state.lastResult.proof_hash,
                transaction_id: state.lastResult.transaction_id
            })
        });

        if (!response.ok) {
            throw new Error("Commit failed");
        }

        const data = await response.json();

        commitBtn.innerText = "Proof On-Chain!";
        commitBtn.style.background = "#22c55e";

        alert(`Block #${data.block_number}\nTx: ${data.tx_hash}`);

    } catch (error) {
        console.error("Commit Error:", error);
        alert("Commit failed.");

        commitBtn.innerText = "Retry Commit";
        commitBtn.disabled = false;
        commitBtn.style.background = "#ef4444";
    }
}


// ===============================
// SPINNER STYLE
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    const style = document.createElement("style");
    style.innerHTML = `
        .hidden { display: none; }

        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid rgba(59, 130, 246, 0.3);
            border-radius: 50%;
            border-top-color: #3b82f6;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);

    console.log("Scanner ready. API:", API_BASE_URL);
});
