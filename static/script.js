// PWA Install Prompt Logic
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    // Show an install button or banner if you have one
    console.log('PWA Install prompt captured');
});

async function installPWA() {
    if (!deferredPrompt) {
        showToast("App is already installed or not supported.", true);
        return;
    }
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to install prompt: ${outcome}`);
    deferredPrompt = null;
}

// Toast Notification
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.innerText = message;
    toast.className = 'show'; // Reset classes
    if (isError) toast.classList.add('error');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

// File Upload Logic
function handleFileUpload() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput.files.length > 0) {
        uploadFile(fileInput.files[0]);
    }
}

function dropHandler(ev) {
    ev.preventDefault();
    document.getElementById('upload-section').classList.remove('dragover');
    if (ev.dataTransfer.items) {
        for (let i = 0; i < ev.dataTransfer.items.length; i++) {
            if (ev.dataTransfer.items[i].kind === 'file') {
                const file = ev.dataTransfer.items[i].getAsFile();
                uploadFile(file);
                break; // only take first file
            }
        }
    }
}

function dragOverHandler(ev) {
    ev.preventDefault();
    document.getElementById('upload-section').classList.add('dragover');
}

function dragLeaveHandler(ev) {
    ev.preventDefault();
    document.getElementById('upload-section').classList.remove('dragover');
}

async function uploadFile(file) {
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
        showToast("Only CSV and Excel files are supported.", true);
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    document.getElementById('upload-info').innerText = "Uploading...";

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        
        if (response.ok) {
            showToast(result.msg);
            document.getElementById('upload-info').innerText = `Uploaded ${file.name} successfully!`;
            document.getElementById('val-patients').innerText = result.rows;
            document.getElementById('val-features').innerText = result.columns.length;
            // auto load charts and dropdown
            populateDropdown();
            loadCharts();
        } else {
            showToast(result.error, true);
            document.getElementById('upload-info').innerText = "";
        }
    } catch (error) {
        showToast("Error uploading file.", true);
    }
}

// Process Data
async function processData() {
    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
    btn.disabled = true;

    try {
        const response = await fetch('/process', { method: 'POST' });
        const result = await response.json();
        if (response.ok) {
            showToast(result.msg);
            // Auto reload charts after processing
            loadCharts();
        } else {
            showToast(result.error, true);
        }
    } catch (error) {
        showToast("Server unreachable or request timed out.", true);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Train Model
async function trainModel() {
    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Training...';
    btn.disabled = true;
    
    document.getElementById('val-accuracy').innerText = "Training...";
    try {
        const response = await fetch('/train', { method: 'POST' });
        const result = await response.json();
        if (response.ok) {
            showToast(result.msg);
            document.getElementById('val-accuracy').innerText = result.accuracy + "%";
        } else {
            showToast(result.error, true);
            document.getElementById('val-accuracy').innerText = "N/A";
        }
    } catch (error) {
        showToast("Training failed or server offline.", true);
        document.getElementById('val-accuracy').innerText = "Error";
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Charts
async function loadCharts() {
    const container = document.getElementById('charts-container');
    container.innerHTML = `
        <div class='chart-container glass' style='display: flex; flex-direction: column; justify-content: center; align-items: center;'>
            <div class="loader"></div>
            <p style="margin-top: 1rem; color: var(--text-muted);">Generating Intelligent Visualizations...</p>
        </div>`;

    try {
        const response = await fetch('/viz_data');
        const result = await response.json();

        if (response.ok && result.charts && result.charts.length > 0) {
            container.innerHTML = ""; // clear loading
            
            result.charts.forEach((chartData, index) => {
                const chartDiv = document.createElement('div');
                chartDiv.id = `chart-${index}`;
                chartDiv.className = 'chart-container glass';
                container.appendChild(chartDiv);

                const trace = {
                    type: chartData.type,
                    name: chartData.title
                };

                if (chartData.type === 'pie') {
                    trace.labels = chartData.labels;
                    trace.values = chartData.values;
                    trace.marker = { colors: ['#0077b6', '#00b4d8', '#48cae4', '#90e0ef', '#caf0f8'] };
                } else if (chartData.type === 'bar') {
                    trace.x = chartData.x;
                    trace.y = chartData.y;
                    trace.marker = { color: '#00b4d8' };
                } else if (chartData.type === 'histogram') {
                    trace.x = chartData.x;
                    trace.marker = { color: '#0077b6' };
                }

                const layout = {
                    title: chartData.title,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { family: 'Inter, sans-serif' },
                    margin: { t: 40, l: 40, r: 20, b: 40 }
                };

                if (chartData.xaxis) layout.xaxis = { title: chartData.xaxis };
                if (chartData.yaxis) layout.yaxis = { title: chartData.yaxis };

                Plotly.newPlot(`chart-${index}`, [trace], layout, {responsive: true});
            });
        } else {
            container.innerHTML = "<div class='chart-container glass' style='display: flex; justify-content: center; align-items: center; color: var(--text-muted);'>No visualization data available. Upload data first.</div>";
        }
    } catch (error) {
        container.innerHTML = "<div class='chart-container glass'>Error loading charts.</div>";
    }
}

// Populate Dropdown
async function populateDropdown() {
    try {
        const response = await fetch('/get_columns');
        const result = await response.json();
        const select = document.getElementById('col-select');
        select.innerHTML = '<option value="">Select a column to visualize...</option>';
        result.columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            option.innerText = col;
            select.appendChild(option);
        });
    } catch (e) {
        console.error("Error loading columns");
    }
}

// Visualize Specific Column
async function visualizeSpecificColumn() {
    const col = document.getElementById('col-select').value;
    if (!col) return showToast("Please select a column.", true);
    
    const container = document.getElementById('charts-container');
    container.innerHTML = "<div class='chart-container glass'>Loading...</div>";
    
    try {
        const response = await fetch('/viz_column', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column: col })
        });
        const result = await response.json();
        
        if (response.ok && result.chart) {
            container.innerHTML = "<div id='single-chart' class='chart-container glass'></div>";
            const layout = {
                title: result.chart.title,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { family: 'Inter, sans-serif' }
            };
            Plotly.newPlot('single-chart', [result.chart], layout, {responsive: true});
        } else {
            showToast(result.error || "Error", true);
        }
    } catch (e) {
        showToast("Error generating chart.", true);
    }
}

// Chatbot
function handleChatKeyPress(event) {
    if (event.key === "Enter") {
        sendQuery();
    }
}

function showTypingIndicator() {
    const box = document.getElementById('chat-box');
    const div = document.createElement('div');
    div.id = 'typing-indicator';
    div.className = 'typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

async function sendQuery() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;

    appendMessage('user', query);
    input.value = "";
    
    showTypingIndicator();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const result = await response.json();
        
        removeTypingIndicator();
        
        if (response.ok) {
            appendMessage('bot', result.response, result.chart_data);
        } else {
            appendMessage('bot', "Sorry, an error occurred.");
        }
    } catch (error) {
        removeTypingIndicator();
        appendMessage('bot', "Connection error.");
    }
}

function appendMessage(sender, text, chartData = null) {
    const box = document.getElementById('chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${sender}`;
    msgDiv.innerText = text;
    box.appendChild(msgDiv);
    
    if (chartData) {
        const chartId = 'chat-chart-' + Date.now();
        const chartDiv = document.createElement('div');
        chartDiv.id = chartId;
        chartDiv.className = 'chat-chart-container';
        box.appendChild(chartDiv);
        
        const layout = {
            title: chartData.title,
            margin: { t: 30, l: 30, r: 10, b: 30 },
            font: { size: 10 }
        };
        // Use timeout to ensure DOM element is ready
        setTimeout(() => {
            Plotly.newPlot(chartId, [chartData], layout, {responsive: true});
            box.scrollTop = box.scrollHeight;
        }, 100);
    }
    
    box.scrollTop = box.scrollHeight;
}

// Sidebar Toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

// Section Switching
function showSection(sectionId) {
    const sections = ['dashboard-content', 'records-content'];
    sections.forEach(id => {
        document.getElementById(id).style.display = (id === sectionId) ? 'block' : 'none';
    });
    
    // Update active state in sidebar
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('onclick') && link.getAttribute('onclick').includes(sectionId)) {
            link.classList.add('active');
        } else if (sectionId === 'dashboard-content' && link.getAttribute('href') === '#') {
             // Handle the first dashboard link which might not have the onclick explicitly the same
             if (link.innerText.includes('Dashboard')) link.classList.add('active');
        }
    });

    if (sectionId === 'records-content') {
        loadRecords();
    }
}

// Load Past Records
async function loadRecords() {
    const list = document.getElementById('records-list');
    try {
        const response = await fetch('/records');
        const data = await response.json();
        
        if (data.records && data.records.length > 0) {
            list.innerHTML = "";
            data.records.reverse().forEach(record => {
                const card = document.createElement('div');
                card.className = 'record-card glass';
                card.innerHTML = `
                    <div class="record-date">${record.date}</div>
                    <div class="record-name">${record.name}</div>
                    <div class="record-summary">${record.summary}</div>
                `;
                list.appendChild(card);
            });
        } else {
            list.innerHTML = "<div class='glass' style='padding: 2rem; text-align: center; color: var(--text-muted);'>No medical records found.</div>";
        }
    } catch (e) {
        list.innerHTML = "<div class='glass' style='padding: 2rem; text-align: center; color: var(--danger);'>Failed to load medical records.</div>";
    }
}

// Profile Modal & History
async function openProfileModal() {
    document.getElementById('profile-modal').classList.add('show');
    // We don't auto-load history anymore, we wait for click
}

function toggleHistory() {
    const section = document.getElementById('history-section');
    if (section.style.display === 'none') {
        section.style.display = 'block';
        loadChatHistory();
    } else {
        section.style.display = 'none';
    }
}

async function loadChatHistory() {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = "<p style='color:var(--text-muted)'>Loading history...</p>";
    
    try {
        const response = await fetch('/history');
        const data = await response.json();
        
        if (data.history && data.history.length > 0) {
            historyList.innerHTML = "";
            data.history.reverse().forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerHTML = `
                    <div style="font-weight: 500;">Q: ${item.query}</div>
                    <div class="history-time">${item.time}</div>
                `;
                historyList.appendChild(div);
            });
        } else {
            historyList.innerHTML = "<p class='text-muted'>No chat history found.</p>";
        }
    } catch (e) {
        historyList.innerHTML = "<p class='text-danger'>Failed to load history.</p>";
    }
}

function closeProfileModal(event) {
    // If event is passed, only close if clicking the overlay
    if (!event || event.target.id === 'profile-modal') {
        document.getElementById('profile-modal').classList.remove('show');
    }
}
