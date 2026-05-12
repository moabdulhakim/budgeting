let recurringPayments = [];

// ===== CSRF =====
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}
const CSRF_TOKEN = window.CSRF_TOKEN || getCookie('csrftoken') || '';

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function _normalizeToastLevel(level) {
    const l = String(level || '').toLowerCase();
    if (l.includes('error') || l.includes('danger')) return 'error';
    if (l.includes('success')) return 'success';
    if (l.includes('warning')) return 'error';
    return 'info';
}

function showServerToasts() {
    const msgs = window.__DJANGO_MESSAGES__ || [];
    if (!Array.isArray(msgs) || !msgs.length) return;
    msgs.forEach(m => showToast(m.text, _normalizeToastLevel(m.level)));
    window.__DJANGO_MESSAGES__ = [];
}

// ===== NAVIGATION =====
function navigate(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');
    document.querySelectorAll('.nav-item').forEach(btn => {
        if (btn.getAttribute('onclick').includes(page)) btn.classList.add('active');
    });
    setTimeout(() => {
        if (page === 'dashboard') initDashboardCharts();
        if (page === 'reports') initReportCharts();
        if (page === 'budget') {
            renderBudgetCards();
            initBudgetChart();
        }
        if (page === 'savings') initSavingsChart();
    }, 100); 
}

// ===== THEME =====
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.dataset.theme === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    html.dataset.theme = newTheme;
    localStorage.setItem('spendo-theme', newTheme); 
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.classList.toggle('on', !isDark);
    setTimeout(() => refreshCharts(), 100);
}
function applySavedTheme() {
    const savedTheme = localStorage.getItem('spendo-theme') || 'light';
    document.documentElement.dataset.theme = savedTheme;
    if (savedTheme === 'dark') {
        const toggle = document.getElementById('theme-toggle');
        if (toggle) toggle.classList.add('on');
    }
}

// ===== DATA INITIALIZATION =====
let transactions = [];
let budgetCategories = [];
let savingsGoals = [];
let currentFilter = "all";

// ===== Signup Logic =====
async function doSignup() {
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-pass').value;
    if (!name || !email || password.length < 6) {
        showToast("Please fill all fields correctly", "error");
        return;
    }
    try {
        const response = await fetch('/api/signup/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify({ username: email, password: password, name: name })
        });
        const result = await response.json();
        
        if (response.ok) {
            showToast(result.message, "success");
            switchTab('login'); 
        } else {
            showToast(result.message, "error");
        }
    } catch (e) {
        showToast("Server error. Check terminal.", "error"); // Fixes the generic failure msg
    }
}
// ===== Deposit to Goal =====
async function depositToGoal(goalId, amount) {
    try {
        const response = await fetch('/api/goals/deposit/', { //
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': CSRF_TOKEN 
            },
            body: JSON.stringify({ goal_id: goalId, amount: amount })
        });

        const result = await response.json().catch(() => ({}));

        if (response.ok && result.success) {
            showToast("Deposit successful!", "success");
            if (result.celebrate) {
                try { runGoalCelebration(); } catch (e) { console.error(e); }
            }
            initApp();
        } else {
            showToast(result.error || "Deposit failed", "error");
        }
    } catch (e) {
        showToast("Error processing deposit", "error");
    }
}

// ===== AUTH LOGIC =====
function validateEmail(email) {
    return String(email)
        .toLowerCase()
        .match(/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/);
}
function launchApp(userData) {
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('app').style.display = 'flex';
    document.getElementById('user-email-sidebar').textContent = userData.email;
    initApp(); 
}

// ===== Login Logic =====  
async function doLogin() {
    const emailField = document.getElementById('login-email');
    const passwordField = document.getElementById('login-password');
    if (!emailField || !passwordField) {
        console.error("Login fields not found in DOM!");
        return;
    }
    const email = emailField.value;
    const password = passwordField.value;
    try {
        const response = await fetch('/api/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify({ username: email, password: password })
        });
        const result = await response.json();
        if (response.ok) {
            launchApp({ name: result.name, email: email });
        } else {
            showToast(result.message || "Invalid credentials", "error");
        }
    } catch (e) {
        showToast("Connection failed", "error");
    }
}

// ===== switch tab =====
function switchTab(tab) {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const tabs = document.querySelectorAll('.auth-tab');
    // Auth pages are separate templates now; keep function harmless
    if (!loginForm || !signupForm || !tabs?.length) return;
    if (tab === 'login') {
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        tabs[0].classList.add('active');
        tabs[1].classList.remove('active');
    } else {
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
        tabs[1].classList.add('active');
        tabs[0].classList.remove('active');
    }
}

function openEditGoal(goalId, name, saved, target) {
    const modal = document.getElementById('goal-modal');
    if (!modal) return;
    document.getElementById("edit-goal-id").value = goalId || "";
    document.getElementById("goal-name").value = name || "";
    document.getElementById("goal-saved").value = saved || "0";
    document.getElementById("goal-target").value = target || "";
    const title = document.getElementById("goal-modal-title");
    const btn = document.getElementById("save-goal-btn");
    if (title) title.textContent = "Edit Savings Goal";
    if (btn) btn.textContent = "Save Changes";
    modal.classList.add("active");
}

// ===== UI RENDERING =====
function renderGoals() {
    const container = document.getElementById('goals-list');
    container.innerHTML = savingsGoals.map((g, index) => {
        const pct = Math.min(Math.round((g.saved / g.target) * 100), 100);
        return `
        <div class="goal-item">
            <div class="goal-header">
                <span class="goal-name">${g.name}</span>
                <span class="goal-pct">${pct}%</span>
            </div>
            <div class="goal-amounts">$${g.saved} of $${g.target}</div>
            <div class="goal-bar-bg">
                <div class="goal-bar-fill" style="width:${pct}%; background:${g.color || '#6c63ff'}"></div>
            </div>
        </div>`;
    }).join('');
}

// ===== RENDER COMPONENTS =====
function renderTransactions(containerId, limit) {
const container = document.getElementById(containerId);
let data = [...transactions];
if(currentFilter === "income"){
    data = data.filter(t => t.amount > 0);
}
else if(currentFilter === "expenses"){
    data = data.filter(t => t.amount < 0);
}
const list = limit ? data.slice(0, limit):data;
container.innerHTML = list.map(tx => `
<div class="tx-item">
<div class="tx-info">
<div class="tx-name">${tx.name}</div>
<div class="tx-date">${tx.category} · ${tx.date}</div>
</div>
<div class="tx-amount ${tx.amount < 0 ? 'expense' : 'income'}">
${tx.amount < 0 ? '-' : '+'}$${Math.abs(tx.amount).toFixed(2)}
</div>
</div>
`).join('');
}

// ===== Filter buttons behavior =====
function setTransactionFilter(filter) {
  currentFilter = filter;
  renderTransactions("all-transactions");
}
function openTxModal() {
  document.getElementById("tx-modal").style.display = "flex";
}
function closeTxModal() {
  document.getElementById("tx-modal").style.display = "none";
}

// ===== BUDGET COMPONENTS =====
function renderBudgetOverview() {
const container = document.getElementById('budget-overview');
container.innerHTML = budgetCategories.slice(0, 5).map(b => {
const pct = Math.min((b.spent / b.budgeted) * 100, 100);
const over = b.spent > b.budgeted;
return `
<div class="budget-item">
<div class="budget-item-header">
<div class="budget-item-left">
<div class="budget-cat-name">${b.name}</div>
</div>
<div class="budget-amounts">$${b.spent} / $${b.budgeted}</div>
</div>
<div class="budget-bar-bg">
<div class="budget-bar-fill" style="width:${pct}%;background:${over ? 'var(--red)' : b.color}"></div>
</div>
</div>
`;
}).join('');
}

function renderGoals() {
    const container = document.getElementById('goals-list');

    container.innerHTML = savingsGoals.map((g, index) => {
        const pct = Math.round((g.saved / g.target) * 100);

        const displayImage = g.image
            ? `<img src="${g.image}" class="goal-img-preview">`
            : `<div class="goal-icon-placeholder">🎯</div>`;

        return `
        <div class="goal-item">
            <button class="edit-goal-btn" onclick="openEditGoalModal(${index})">✏️</button>
            <div class="goal-header">
                <div class="goal-name-row">
                    ${displayImage} <span class="goal-name">${g.name}</span>
                </div>
                <span class="goal-pct">${pct}%</span>
            </div>
            <div class="goal-amounts">$${g.saved.toLocaleString()} of $${g.target.toLocaleString()}</div>
            <div class="goal-bar-bg">
                <div class="goal-bar-fill" style="width:${pct}%;background:linear-gradient(90deg,${g.color},${g.color}99)"></div>
            </div>
        </div>
        `;
    }).join('');
}

document.addEventListener('change', function(e) {
    if (e.target && e.target.id === 'goal-image-input') {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                document.getElementById('goal-image-url').value = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    }
});

function renderBudgetCards() {
const container = document.getElementById('budget-cards');
container.innerHTML = budgetCategories.map(b => {
const pct = Math.min(Math.round((b.spent / b.budgeted) * 100), 100);
const over = b.spent > b.budgeted;
const remaining = b.budgeted - b.spent;
return `
<div class="stat-card">
<div class="stat-header">
<div style="display:flex;align-items:center;gap:10px">
<div>
<div style="font-size:13px;font-weight:600">${b.name}</div>
<div style="font-size:11px;color:var(--text3)">${pct}% used</div>
</div>
</div>
<span class="status-pill ${over ? 'status-over' : pct > 80 ? 'status-warn' : 'status-ok'}">${over ? 'Over' : pct > 80 ? 'Near' : 'OK'}</span>
</div>
<div class="budget-bar-bg" style="margin:12px 0 8px">
<div class="budget-bar-fill" style="width:${pct}%;background:${over ? 'var(--red)' : b.color}"></div>
</div>
<div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text2)">
<span>$${b.spent} spent</span>
<span>${over ? '<span style=color:var(--red)>$'+Math.abs(remaining)+' over</span>' : '$'+remaining+' left'}</span>
</div>
</div>
`;
}).join('');
}

// ===== CATEGORY MODAL =====
function addCategory() {
document.getElementById("category-modal").classList.add("active");
}
function closeCatModal() {
document.getElementById("category-modal").classList.remove("active");
}
async function saveCategory() {
    const name = document.getElementById("cat-name").value;
    const budgeted = document.getElementById("cat-budget").value;

    if (!name || !budgeted) {
        showToast("Please fill all fields", "error");
        return;
    }
    try {
        const response = await fetch('/api/categories/add/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify({ name, budgeted }) 
        });
        if (response.ok) {
            showToast("Category added!", "success");
            initApp(); 
            closeCatModal();
        }
    } catch (e) {
        showToast("Error saving category", "error");
    }
}

// ===== GOAL MODAL =====
function addGoal() {
    document.getElementById("edit-goal-id").value = "";
    document.getElementById("goal-name").value = "";
    document.getElementById("goal-saved").value = "0";
    document.getElementById("goal-target").value = "";
    document.getElementById("goal-modal-title").textContent = "Add New Savings Goal";
    document.getElementById("save-goal-btn").textContent = "Add Goal";
    document.getElementById("goal-modal").classList.add("active");
}

function saveGoal() {
    const name = document.getElementById("goal-name").value;
    const saved = Number(document.getElementById("goal-saved").value);
    const target = Number(document.getElementById("goal-target").value);
    const editId = document.getElementById("edit-goal-id").value;
    const imageUrl = document.getElementById("goal-image-url").value;

    if (!name.trim()) {
        showToast("Goal name required", "error");
        return;
    }

    if (target <= 0) {
        showToast("Target must be greater than 0", "error");
        return;
    }

    const goalData = {
        name: name,
        target: target,
        saved: saved,
        image: imageUrl || null,
        color: "#6c63ff"
    };

    if (saved >= target && target > 0) {
        const duration = 3 * 1000;
        const end = Date.now() + duration;

        (function frame() {
            confetti({
                particleCount: 5,
                angle: 60,
                spread: 55,
                origin: { x: 0, y: 0.7 },
                colors: ['#6c63ff', '#a855f7', '#22c55e']
            });
            confetti({
                particleCount: 5,
                angle: 120,
                spread: 55,
                origin: { x: 1, y: 0.7 },
                colors: ['#6c63ff', '#a855f7', '#22c55e']
            });
            if (Date.now() < end) {
                requestAnimationFrame(frame);
            }
        }());

        setTimeout(() => {
            showToast(`Goal Achieved!: ${name}`, "success");
        }, 1000);
    }

    if (editId !== "") {
        savingsGoals[editId] = goalData;
    } else {
        savingsGoals.push(goalData);
    }

    closeGoalModal();
    renderGoals();
    initSavingsChart();

    document.getElementById("goal-image-input").value = "";
    document.getElementById("goal-image-url").value = "";

    showToast("Goal saved successfully", "success");
}


function closeGoalModal() {
document.getElementById("goal-modal").classList.remove("active");
}

function openEditGoalModal(index) {
    const goal = savingsGoals[index];
    document.getElementById("edit-goal-id").value = index;
    document.getElementById("goal-name").value = goal.name;
    document.getElementById("goal-saved").value = goal.saved;
    document.getElementById("goal-target").value = goal.target;
    document.getElementById("goal-modal-title").textContent = "Edit Goal";
    document.getElementById("save-goal-btn").textContent = "Save Changes";
    document.getElementById("goal-modal").classList.add("active");
}

// ===== REPORTS =====
function renderReportTable() {
const tbody = document.getElementById('report-table');
tbody.innerHTML = budgetCategories.map(b => {
const remaining = b.budgeted - b.spent;
const over = b.spent > b.budgeted;
const pct = Math.round((b.spent / b.budgeted) * 100);
return `
<tr>
<td> ${b.name}</td>
<td style="font-family:'JetBrains Mono',monospace">$${b.budgeted.toLocaleString()}</td>
<td style="font-family:'JetBrains Mono',monospace">$${b.spent.toLocaleString()}</td>
<td style="font-family:'JetBrains Mono',monospace;color:${over ? 'var(--red)' : 'var(--green)'}">
${over ? '-' : '+'}$${Math.abs(remaining).toLocaleString()}
</td>
<td><span class="status-pill ${over ? 'status-over' : pct > 80 ? 'status-warn' : 'status-ok'}">${over ? 'Over Budget' : pct > 80 ? 'Near Limit' : 'On Track'}</span></td>
</tr>
`;
}).join('');
}

// ===== CHARTS =====
const chartInstances = {};
function getColors() {
const isDark = document.documentElement.dataset.theme === 'dark';
return {
grid: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
text: isDark ? '#9ba3c0' : '#6b7090',
accent: '#6c63ff',
red: isDark ? '#f87171' : '#ef4444',
green: isDark ? '#34d399' : '#22c55e',
blue: isDark ? '#60a5fa' : '#3b82f6',
orange: isDark ? '#fbbf24' : '#f59e0b',
purple: isDark ? '#c084fc' : '#a855f7',
};
}
function destroyChart(id) {
if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; }
}

// ==== Dashboard Donut Chart & Report Trend Chart ==== 
function initDashboardCharts() {
    const c = getColors();
    const donutCanvas = document.getElementById('categoryDonutChart');
    const labelsAttr = donutCanvas?.dataset?.labels;
    const valuesAttr = donutCanvas?.dataset?.values;
    const labels = labelsAttr ? _safeJsonParse(labelsAttr, []) : budgetCategories.map(b => b.name);
    const dataValues = valuesAttr ? _safeJsonParse(valuesAttr, []) : budgetCategories.map(b => b.spent);

    // Donut chart 
    if (!donutCanvas || typeof Chart === 'undefined') return;
    destroyChart('categoryDonutChart');
    chartInstances['categoryDonutChart'] = new Chart(
        donutCanvas,
        {
            type: 'doughnut',
            data: {
                labels: labels.length ? labels : ['No Data'],
                datasets: [{
                    data: dataValues.length ? dataValues : [1],
                    backgroundColor: [c.orange, c.accent, c.blue, c.purple, c.green, '#94a3b8'],
                    borderWidth: 0,
                    hoverOffset: 8,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: c.text, font: { family: 'Sora', size: 11 }, boxWidth: 10, padding: 12 }
                    }
                }
            }
        }
    );
    }

function initIncomeExpenseChart() {
    const canvas = document.getElementById('incomeExpenseChart');
    if (!canvas || typeof Chart === 'undefined') return;
    const c = getColors();
    const labels = _safeJsonParse(canvas.dataset.labels || '', []);
    const income = _safeJsonParse(canvas.dataset.income || '', []);
    const expenses = _safeJsonParse(canvas.dataset.expenses || '', []);
    destroyChart('incomeExpenseChart');
    chartInstances['incomeExpenseChart'] = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels.length ? labels : ['No Data'],
            datasets: [
                {
                    label: 'Income',
                    data: income,
                    borderColor: c.accent,
                    backgroundColor: c.accent + '20',
                    tension: 0.35,
                    fill: true,
                    pointRadius: 3,
                    pointBackgroundColor: c.accent,
                },
                {
                    label: 'Expenses',
                    data: expenses,
                    borderColor: c.red,
                    backgroundColor: c.red + '15',
                    tension: 0.35,
                    fill: true,
                    pointRadius: 3,
                    pointBackgroundColor: c.red,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: c.grid }, ticks: { color: c.text } },
                y: {
                    grid: { color: c.grid },
                    ticks: { color: c.text, callback: v => '$' + Number(v).toLocaleString() },
                },
            },
        },
    });
}

// ===== Trend Chart in Reports =====         
function initReportCharts() {
    const c = getColors();
    if (typeof Chart === 'undefined') return;

    // Template-rendered reports page defines globals: trendData, pieData, weeklyData
    const trendCanvas = document.getElementById('trendChart');
    if (trendCanvas && window.trendData) {
        destroyChart('trendChart');
        chartInstances['trendChart'] = new Chart(trendCanvas, {
            type: 'line',
            data: {
                labels: window.trendData.labels || [],
                datasets: [
                    {
                        label: 'Income',
                        data: window.trendData.income || [],
                        borderColor: c.green,
                        backgroundColor: c.green + '20',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointBackgroundColor: c.green,
                    },
                    {
                        label: 'Expenses',
                        data: window.trendData.expenses || [],
                        borderColor: c.red,
                        backgroundColor: c.red + '15',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointBackgroundColor: c.red,
                    },
                    {
                        label: 'Savings',
                        data: window.trendData.savings || [],
                        borderColor: c.accent,
                        backgroundColor: c.accent + '12',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointBackgroundColor: c.accent,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: true, labels: { color: c.text } } },
                scales: {
                    x: { grid: { color: c.grid }, ticks: { color: c.text } },
                    y: { grid: { color: c.grid }, ticks: { color: c.text, callback: v => '$' + Number(v).toLocaleString() } },
                },
            },
        });
    }

    const pieCanvas = document.getElementById('reportPieChart');
    if (pieCanvas && window.pieData) {
        destroyChart('reportPieChart');
        chartInstances['reportPieChart'] = new Chart(pieCanvas, {
            type: 'doughnut',
            data: {
                labels: window.pieData.labels || [],
                datasets: [
                    {
                        data: window.pieData.values || [],
                        backgroundColor: [c.orange, c.accent, c.blue, c.purple, c.green, '#94a3b8'],
                        borderWidth: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: { legend: { position: 'bottom', labels: { color: c.text, boxWidth: 10 } } },
            },
        });
    }

    const weeklyCanvas = document.getElementById('weeklyChart');
    if (weeklyCanvas && window.weeklyData) {
        destroyChart('weeklyChart');
        chartInstances['weeklyChart'] = new Chart(weeklyCanvas, {
            type: 'bar',
            data: {
                labels: window.weeklyData.labels || [],
                datasets: [
                    {
                        label: 'Spent',
                        data: window.weeklyData.values || [],
                        backgroundColor: c.red + '90',
                        borderRadius: 8,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: c.text } },
                    y: { grid: { color: c.grid }, ticks: { color: c.text, callback: v => '$' + Number(v).toLocaleString() } },
                },
            },
        });
    }
}


function initBudgetChart() {
    const c = getColors();
    const canvas = document.getElementById('budgetBarChart');
    if (!canvas || typeof Chart === 'undefined') return;
    const labels = _safeJsonParse(canvas.dataset.labels || '', []);
    const budgeted = _safeJsonParse(canvas.dataset.budgeted || '', []);
    const spent = _safeJsonParse(canvas.dataset.spent || '', []);
    destroyChart('budgetBarChart');
    chartInstances['budgetBarChart'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : budgetCategories.map(b => b.name),
            datasets: [
                {
                    label: 'Budgeted',
                    data: budgeted.length ? budgeted : budgetCategories.map(b => b.budgeted),
                    backgroundColor: c.accent + '40',
                    borderColor: c.accent,
                    borderWidth: 2,
                    borderRadius: 8,
                },
                {
                    label: 'Spent',
                    data: spent.length ? spent : budgetCategories.map(b => b.spent),
                    backgroundColor: (spent.length ? spent : budgetCategories.map(b => b.spent)).map((v, i) => {
                        const b = budgeted.length ? budgeted[i] : budgetCategories[i]?.budgeted;
                        return Number(v) > Number(b) ? c.red + '99' : c.green + '99';
                    }),
                    borderColor: (spent.length ? spent : budgetCategories.map(b => b.spent)).map((v, i) => {
                        const b = budgeted.length ? budgeted[i] : budgetCategories[i]?.budgeted;
                        return Number(v) > Number(b) ? c.red : c.green;
                    }),
                    borderWidth: 2,
                    borderRadius: 8,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: c.grid }, ticks: { color: c.text } },
                x: { grid: { display: false }, ticks: { color: c.text } }
            }
        }
    });
}

// ===== Savings Chart in Goals =====
function initSavingsChart() {
    const c = getColors();
    const canvas = document.getElementById('savingsChart');
    if (!canvas || typeof Chart === 'undefined') return;
    const labels = _safeJsonParse(canvas.dataset.labels || '', []);
    const saved = _safeJsonParse(canvas.dataset.saved || '', []);
    const targets = _safeJsonParse(canvas.dataset.targets || '', []);
    destroyChart('savingsChart');
    chartInstances['savingsChart'] = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : savingsGoals.map(g => g.name),
            datasets: [
                {
                    label: 'Target',
                    data: targets.length ? targets : savingsGoals.map(g => g.target),
                    backgroundColor: c.accent + '30',
                    borderColor: c.accent,
                    borderWidth: 2,
                    borderRadius: 8,
                },
                {
                    label: 'Saved',
                    data: saved.length ? saved : savingsGoals.map(g => g.saved),
                    backgroundColor: c.green + '99',
                    borderColor: c.green,
                    borderWidth: 2,
                    borderRadius: 8,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: c.text } } },
            scales: {
                x: { grid: { display: false }, ticks: { color: c.text } },
                y: { grid: { color: c.grid }, ticks: { color: c.text, callback: v => '$' + (v/1000).toFixed(0) + 'k' } }
            }
        }
    });
}

//
function refreshCharts() {
    const activePage = document.querySelector('.page.active')?.id;
    if (!activePage) return;
    switch (activePage) {
        case 'page-dashboard':
            initDashboardCharts(); 
            break;
        case 'page-reports':
            initReportCharts(); 
            break;
        case 'page-budget':
            initBudgetChart(); 
            break;
        case 'page-savings':
            initSavingsChart(); 
            break;
    }
}

// Filter buttons behavior
document.addEventListener('click', e => {
if (e.target.classList.contains('filter-btn')) {
const parent = e.target.closest('.filter-bar');
parent.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
e.target.classList.add('active');
}
});

// ============ Budget Limits =========
function checkBudgetLimits() {
    const alertBanner = document.getElementById('limit-alert');
    const categorySpan = document.getElementById('alert-category-name');
    if (!alertBanner || !categorySpan) return;
    const overBudgetNames = budgetCategories
        .filter(cat => (cat.spent / cat.budgeted) >= 0.9)
        .map(cat => cat.name);
    if (overBudgetNames.length > 0) {
        const namesText = overBudgetNames.length > 1
            ? overBudgetNames.slice(0, -1).join(', ') + ' & ' + overBudgetNames.slice(-1)
            : overBudgetNames[0];
        categorySpan.textContent = namesText;
        alertBanner.style.display = 'flex';
    } else {
        alertBanner.style.display = 'none';
    }
}

// ============ UpcomingPayments =========
function checkUpcomingPayments() {
    var alertBanner = document.getElementById('upcoming-payment-alert');
    var alertMsg = document.getElementById('payment-details-msg');
    if (!alertBanner || !alertMsg) return;
    var today = new Date();
    var currentDay = today.getDate();
    var upcomingPayments = recurringPayments.filter(function(p) {
        var diff = p.dayOfMonth >= currentDay ? p.dayOfMonth - currentDay : (30 - currentDay + p.dayOfMonth);
        return diff > 0 && diff <= 10;
    });
    if (upcomingPayments.length > 0) {
        var message = "<strong>Upcoming Payment:</strong> You'll need ";
        for (var i = 0; i < upcomingPayments.length; i++) {
            var p = upcomingPayments[i];
            var daysLeft = p.dayOfMonth - currentDay;
            message += "<strong>$" + p.amount + "</strong> for " + p.name + " in <strong>" + daysLeft + " days</strong>";
            if (i < upcomingPayments.length - 1) {
                message += " and ";
            }
        }
        alertMsg.innerHTML = message;
        alertBanner.style.display = 'flex';
    } else {
        alertBanner.style.display = 'none';
    }
}

function _safeJsonParse(raw, fallback) {
    try {
        return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
        console.warn('JSON parse failed', e);
        return fallback;
    }
}

// current date (full weekday + date)
function updateCurrentMonthDisplay() {
    const displayElement = document.getElementById('current-date-display');
    const budgetDateElement = document.getElementById('current-budget-date');
    if (!displayElement) return;
    const now = new Date();
    const dateString = now.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });
    displayElement.textContent = dateString;
    if (budgetDateElement) {
        const monthYear = now.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        budgetDateElement.textContent = monthYear;
    }
}

function scheduleTimedDashboardAlerts() {
    document.querySelectorAll('.js-timed-dashboard-alert').forEach((el) => {
        window.setTimeout(() => {
            el.classList.add('dashboard-alert--fadeout');
            const hide = () => {
                el.style.display = 'none';
                el.removeEventListener('transitionend', onEnd);
            };
            const onEnd = (ev) => {
                if (ev.propertyName === 'opacity') hide();
            };
            el.addEventListener('transitionend', onEnd);
            window.setTimeout(hide, 600);
        }, 120000);
    });
}

function syncTxDueVisibility() {
    const cb = document.getElementById('tx-upcoming');
    const wrap = document.getElementById('tx-due-wrap');
    const due = document.getElementById('tx-due-date');
    if (!cb || !wrap) return;
    wrap.style.display = cb.checked ? 'block' : 'none';
    if (!cb.checked && due) due.value = '';
}

function resetTransactionModal() {
    const form = document.getElementById('tx-form');
    const title = document.getElementById('tx-modal-title');
    const btn = document.getElementById('tx-submit-btn');
    if (form && window.__TX_ADD_URL__) form.action = window.__TX_ADD_URL__;
    if (title) title.textContent = 'Add Transaction';
    if (btn) btn.textContent = 'Add Transaction';
    const name = document.getElementById('tx-name');
    const amt = document.getElementById('tx-amount');
    const typ = document.getElementById('tx-type');
    const cat = document.getElementById('tx-category');
    const dt = document.getElementById('tx-date');
    const due = document.getElementById('tx-due-date');
    const cb = document.getElementById('tx-upcoming');
    if (name) name.value = '';
    if (amt) amt.value = '';
    if (typ) typ.value = 'expense';
    if (cat) cat.value = '';
    if (dt) dt.value = '';
    if (due) due.value = '';
    if (cb) cb.checked = false;
    syncTxDueVisibility();
}

function closeTransactionModal() {
    const m = document.getElementById('tx-modal');
    if (m) m.classList.remove('active');
    resetTransactionModal();
}

function openNewTransactionModal() {
    resetTransactionModal();
    document.getElementById('tx-modal')?.classList.add('active');
}

function openEditTransactionModalFromBtn(btn) {
    const raw = btn.getAttribute('data-tx-json');
    if (!raw) return;
    let tx;
    try {
        tx = JSON.parse(raw);
    } catch (e) {
        console.error(e);
        return;
    }
    openEditTransactionModal(tx);
}

function openEditTransactionModal(tx) {
    const form = document.getElementById('tx-form');
    const title = document.getElementById('tx-modal-title');
    const btn = document.getElementById('tx-submit-btn');
    const tmpl = window.__TX_UPDATE_TMPL__ || '';
    if (form && tmpl) form.action = tmpl.replace('888888888', String(tx.id));
    if (title) title.textContent = 'Edit Transaction';
    if (btn) btn.textContent = 'Save Changes';
    document.getElementById('tx-name').value = tx.name || '';
    document.getElementById('tx-amount').value = tx.amount ?? '';
    document.getElementById('tx-type').value = tx.type || 'expense';
    const categorySelect = document.getElementById('tx-category');
    if (categorySelect) {
        const txCategory = tx.category || '';
        if (txCategory && !Array.from(categorySelect.options).some(o => o.value === txCategory)) {
            const dynamicOption = document.createElement('option');
            dynamicOption.value = txCategory;
            dynamicOption.textContent = txCategory;
            categorySelect.appendChild(dynamicOption);
        }
        categorySelect.value = txCategory;
    }
    document.getElementById('tx-date').value = tx.date_iso || '';
    document.getElementById('tx-upcoming').checked = !!tx.is_upcoming;
    document.getElementById('tx-due-date').value = tx.due_iso || '';
    syncTxDueVisibility();
    document.getElementById('tx-modal')?.classList.add('active');
}

function resetCategoryModal() {
    const title = document.getElementById('category-modal-title');
    const bid = document.getElementById('cat-id');
    const btn = document.getElementById('category-save-btn');
    if (bid) bid.value = '';
    if (title) title.textContent = 'Add Budget Category';
    if (btn) btn.textContent = 'Save Category';
    const n = document.getElementById('cat-name');
    const b = document.getElementById('cat-budget');
    if (n) n.value = '';
    if (b) b.value = '';
}

function closeCategoryModal() {
    document.getElementById('category-modal')?.classList.remove('active');
    resetCategoryModal();
}

function openNewCategoryModal() {
    resetCategoryModal();
    document.getElementById('category-modal')?.classList.add('active');
}

function openEditCategoryFromBtn(btn) {
    const id = btn.getAttribute('data-cat-id');
    const name = btn.getAttribute('data-cat-name') || '';
    const budget = btn.getAttribute('data-cat-budget') || '';
    openEditCategoryModal(id, name, budget);
}

function openEditCategoryModal(id, name, budget) {
    const title = document.getElementById('category-modal-title');
    const bid = document.getElementById('cat-id');
    const btn = document.getElementById('category-save-btn');
    if (title) title.textContent = 'Edit Budget Category';
    if (btn) btn.textContent = 'Save Changes';
    if (bid) bid.value = id || '';
    document.getElementById('cat-name').value = name || '';
    document.getElementById('cat-budget').value = budget || '';
    document.getElementById('category-modal')?.classList.add('active');
}

function runGoalCelebration() {
    if (typeof confetti !== 'function') {
        showToast('Congratulations! Goal completed!', 'success');
        return;
    }
    const end = Date.now() + 1600;
    (function frame() {
        confetti({
            particleCount: 4,
            angle: 60,
            spread: 55,
            origin: { x: 0, y: 0.65 },
            colors: ['#6c63ff', '#a855f7', '#22c55e'],
        });
        confetti({
            particleCount: 4,
            angle: 120,
            spread: 55,
            origin: { x: 1, y: 0.65 },
            colors: ['#6c63ff', '#a855f7', '#22c55e'],
        });
        if (Date.now() < end) requestAnimationFrame(frame);
    })();
    showToast('Congratulations! You reached your savings goal!', 'success');
    try {
        history.replaceState(null, '', window.location.pathname);
    } catch (e) { /* ignore */ }
}

// ===== INIT =====
function initApp() {
renderTransactions('recent-tx', 6);
renderTransactions('all-transactions');
renderBudgetOverview();
renderGoals();
renderBudgetCards();
renderReportTable();
checkBudgetLimits();
checkUpcomingPayments();
updateCurrentMonthDisplay();
setTimeout(() => initDashboardCharts(), 100);
}

if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = 'Sora';
}

// ===== PAGE BOOTSTRAP (template pages) =====
document.addEventListener('DOMContentLoaded', () => {
    try { applySavedTheme(); } catch { /* ignore */ }
    try { showServerToasts(); } catch { /* ignore */ }
    try {
        updateCurrentMonthDisplay();
        window.setInterval(updateCurrentMonthDisplay, 60000);
    } catch { /* ignore */ }
    try { scheduleTimedDashboardAlerts(); } catch { /* ignore */ }
    try {
        document.getElementById('tx-upcoming')?.addEventListener('change', syncTxDueVisibility);
    } catch { /* ignore */ }
    if (window.__CELEBRATE_GOAL__) {
        try { runGoalCelebration(); } catch (e) { console.error(e); }
        delete window.__CELEBRATE_GOAL__;
    }
    // Charts (only initialize if canvas exists on that page)
    try {
        initIncomeExpenseChart();
        initDashboardCharts();
        initBudgetChart();
        initSavingsChart();
        initReportCharts();
    } catch (e) {
        // Avoid breaking the whole page if a single chart fails
        console.error(e);
    }

    // ===== CHATBOT WIDGET =====
    initChatbot();
});

// ===== Chatbot Widget =====
function initChatbot() {
    const fab      = document.getElementById('chatbot-fab');
    const panel    = document.getElementById('chatbot-panel');
    const closeBtn = document.getElementById('chatbot-close');
    const input    = document.getElementById('chatbot-input');
    const send     = document.getElementById('chatbot-send');
    const msgs     = document.getElementById('chatbot-messages');
    const chips    = document.querySelectorAll('.chat-chip');

    if (!fab || !panel) return; // widget not in DOM (unauthenticated pages)

    let isOpen = false;

    function togglePanel() {
        isOpen = !isOpen;
        panel.classList.toggle('open', isOpen);
        if (isOpen) {
            if (msgs.children.length === 0) {
                appendBot("👋 Hi! I'm Spendo Assistant. Ask me about your balance, spending, goals, bills, or tips!");
            }
            setTimeout(() => input.focus(), 150);
        }
    }

    function appendMsg(text, role) {
        const div = document.createElement('div');
        div.className = `chat-msg ${role}`;
        div.textContent = text;
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
        return div;
    }

    function appendBot(text)  { return appendMsg(text, 'bot'); }
    function appendUser(text) { return appendMsg(text, 'user'); }

    async function sendMessage(text) {
        text = (text || '').trim();
        if (!text) return;

        appendUser(text);
        input.value = '';
        send.disabled = true;

        const typing = appendMsg('Thinking…', 'typing');

        try {
            const res = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                },
                body: JSON.stringify({ message: text }),
            });
            const data = await res.json();
            typing.remove();
            appendBot(data.reply || 'Sorry, I had trouble answering that.');
        } catch {
            typing.remove();
            appendBot('⚠️ Connection error. Please try again.');
        } finally {
            send.disabled = false;
            input.focus();
        }
    }

    fab.addEventListener('click', togglePanel);
    closeBtn.addEventListener('click', togglePanel);
    send.addEventListener('click', () => sendMessage(input.value));
    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input.value);
        }
    });
    chips.forEach(chip => {
        chip.addEventListener('click', () => sendMessage(chip.dataset.msg));
    });
}

