let recurringPayments = []; // تعريف المتغير لمنع الخطأ

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
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
    document.getElementById('theme-toggle').classList.toggle('on', !isDark);
    setTimeout(() => refreshCharts(), 100);
}
function applySavedTheme() {
    const savedTheme = localStorage.getItem('spendo-theme') || 'light';
    document.documentElement.dataset.theme = savedTheme;
    if (savedTheme === 'dark') {
        document.getElementById('theme-toggle').classList.add('on');
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
        
        if (response.ok) {
            showToast("Deposit successful!", "success");
            initApp();
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
    document.getElementById('auth-screen').style.display = 'none'; // إخفاء اللوجين
    document.getElementById('app').style.display = 'flex'; // إظهار التطبيق
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

// ===== BUDGET CARDS =====
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
    const labels = budgetCategories.map(b => b.name);
    const dataValues = budgetCategories.map(b => b.spent);

    // Donut chart 
    destroyChart('categoryDonutChart');
    chartInstances['categoryDonutChart'] = new Chart(
        document.getElementById('categoryDonutChart'),
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

// ===== Trend Chart in Reports =====         
function initReportCharts() {
    const c = getColors();
    const incomeData = transactions.filter(t => t.amount > 0).map(t => t.amount);
    const expenseData = transactions.filter(t => t.amount < 0).map(t => Math.abs(t.amount));
    const labels = transactions.map(t => t.date);
    destroyChart('trendChart');
    chartInstances['trendChart'] = new Chart(document.getElementById('trendChart'), {
        type: 'line',
        data: {
            labels: labels.length ? labels : ['No Data'],
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    borderColor: c.green, backgroundColor: c.green + '20',
                    tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: c.green,
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    borderColor: c.red, backgroundColor: c.red + '15',
                    tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: c.red,
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: true, labels: { color: c.text } } },
            scales: {
                x: { grid: { color: c.grid }, ticks: { color: c.text } },
                y: { grid: { color: c.grid }, ticks: { color: c.text, callback: v => '$' + v.toLocaleString() } }
            }
        }
    });
        initReportPieChart(c);
}


function initBudgetChart() {
    const c = getColors();
    destroyChart('budgetBarChart');
    chartInstances['budgetBarChart'] = new Chart(document.getElementById('budgetBarChart'), {
        type: 'bar',
        data: {
            labels: budgetCategories.map(b => b.name),
            datasets: [
                {
                    label: 'Budgeted',
                    data: budgetCategories.map(b => b.budgeted),
                    backgroundColor: c.accent + '40',
                    borderColor: c.accent,
                    borderWidth: 2,
                    borderRadius: 8,
                },
                {
                    label: 'Spent',
                    data: budgetCategories.map(b => b.spent),
                    backgroundColor: budgetCategories.map(b => b.spent > b.budgeted ? c.red + '99' : c.green + '99'),
                    borderColor: budgetCategories.map(b => b.spent > b.budgeted ? c.red : c.green),
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
    destroyChart('savingsChart');
    chartInstances['savingsChart'] = new Chart(document.getElementById('savingsChart'), {
        type: 'bar',
        data: {
            labels: savingsGoals.map(g => g.name),
            datasets: [
                {
                    label: 'Target',
                    data: savingsGoals.map(g => g.target),
                    backgroundColor: c.accent + '30',
                    borderColor: c.accent,
                    borderWidth: 2,
                    borderRadius: 8,
                },
                {
                    label: 'Saved',
                    data: savingsGoals.map(g => g.saved),
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

// current date
function updateCurrentMonthDisplay() {
    const displayElement = document.getElementById('current-date-display');
    if (!displayElement) return;
    const now = new Date();
    const options = { month: 'long', year: 'numeric' };
    const dateString = now.toLocaleDateString('en-US', options);
    displayElement.textContent = `📅 ${dateString}`;
}

// ===== Save Transaction =====
async function saveTransaction() {
    const type = document.getElementById('tx-type').value;
    const name = document.getElementById('tx-name').value;
    const amount = document.getElementById('tx-amount').value;
    const category = document.getElementById('tx-category').value;
    try {
        const response = await fetch('/api/transactions/add/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body: JSON.stringify({ type, name, amount: parseFloat(amount), category })
        });
        if (response.ok) {
            showToast("Transaction added!", "success");
            closeModal('tx-modal');
            initApp(); // Refresh data immediately
        }
    } catch (e) {
        showToast("Error saving transaction", "error");
    }
}

async function initApp() {
    try {
        const response = await fetch('/api/dashboard/'); // Your Django URL
        if (response.ok) {
            const data = await response.json();
                updateDashboardUI(data); 
            transactions = data.transactions || [];
            budgetCategories = data.categories || [];
            savingsGoals = data.goals || [];
            recurringPayments = data.upcoming || [];

            renderTransactions('recent-tx', 6);
            renderBudgetOverview();
            renderGoals();
            checkBudgetLimits();
            checkUpcomingPayments();
            updateCurrentMonthDisplay();
            initDashboardCharts(); 
        }
    } catch (e) {
        console.error("Error loading real data:", e);
        showToast("Could not sync with database", "error");
    }
}

// ===== Update Dashboard UI =====
function updateDashboardUI(data) {
    document.getElementById('total-balance').textContent = `$${(data.balance || 0).toLocaleString()}`;
    document.getElementById('monthly-income').textContent = `$${(data.income || 0).toLocaleString()}`;
    document.getElementById('monthly-expenses').textContent = `$${(data.expenses || 0).toLocaleString()}`;
        const savingsRate = data.income > 0 ? 
        (((data.income - data.expenses) / data.income) * 100).toFixed(1) : 0;
    document.getElementById('savings-rate').textContent = `${savingsRate}%`;

    // 3. Update Greeting Name (The name next to "Welcome back")
    if (data.user && data.user.name) {
        document.getElementById('greet-name').textContent = data.user.name.split(' ')[0];
    }
}

// ===== LOGOUT =====
async function doLogout() {
    try {
        const response = await fetch('/api/logout/', {
            method: 'POST',
            headers: { 'X-CSRFToken': CSRF_TOKEN }
        });
        if (response.ok) {
            document.getElementById('app').style.display = 'none';
            document.getElementById('auth-screen').style.display = 'flex';
            showToast("Logged out successfully", "success");
        }
    } catch (e) {
        showToast("Logout failed", "error");
    }
}