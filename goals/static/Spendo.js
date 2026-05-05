let transactions = [
{ name: 'Netflix Subscription', category: 'Entertainment', date: 'Apr 28', amount: -15.99, color: '#ef4444', bg: 'var(--red-bg)' },
{ name: 'Grocery Store', category: 'Food', date: 'Apr 27', amount: -89.50, color: '#f59e0b', bg: 'var(--orange-bg)' },
{ name: 'Monthly Salary', category: 'Income', date: 'Apr 26', amount: 7200.00, color: '#22c55e', bg: 'var(--green-bg)' },
{ name: 'Electric Bill', category: 'Utilities', date: 'Apr 25', amount: -124.00, color: '#f59e0b', bg: 'var(--orange-bg)' },
{ name: 'Uber Ride', category: 'Transport', date: 'Apr 24', amount: -23.50, color: '#3b82f6', bg: 'var(--blue-bg)' },
{ name: 'Amazon Purchase', category: 'Shopping', date: 'Apr 23', amount: -156.99, color: '#a855f7', bg: 'var(--purple-bg)' },
{ name: 'Coffee Shop', category: 'Food', date: 'Apr 22', amount: -6.50, color: '#f59e0b', bg: 'var(--orange-bg)' },
{ name: 'Gym Membership', category: 'Health', date: 'Apr 21', amount: -49.99, color: '#22c55e', bg: 'var(--green-bg)' },
{ name: 'Freelance Payment', category: 'Income', date: 'Apr 20', amount: 800.00, color: '#22c55e', bg: 'var(--green-bg)' },
{ name: 'Restaurant Dinner', category: 'Food', date: 'Apr 19', amount: -72.00, color: '#f59e0b', bg: 'var(--orange-bg)' },
{ name: 'Phone Bill', category: 'Utilities', date: 'Apr 18', amount: -65.00, color: '#f59e0b', bg: 'var(--orange-bg)' },
{ name: 'Movie Tickets', category: 'Entertainment', date: 'Apr 17', amount: -28.00, color: '#ef4444', bg: 'var(--red-bg)' },
];

let budgetCategories = [
{ name: 'Food & Dining', budgeted: 1000, spent: 700, color: '#f59e0b', bg: 'var(--orange-bg)' },
{ name: 'Housing', budgeted: 1800, spent: 1800, color: '#6c63ff', bg: 'var(--accent-glow)' },
{ name: 'Transport', budgeted: 400, spent: 280, color: '#3b82f6', bg: 'var(--blue-bg)' },
{ name: 'Entertainment', budgeted: 300, spent: 290, color: '#ef4444', bg: 'var(--red-bg)' },
{ name: 'Shopping', budgeted: 600, spent: 520, color: '#a855f7', bg: 'var(--purple-bg)' },
{ name: 'Health', budgeted: 250, spent: 190, color: '#22c55e', bg: 'var(--green-bg)' },
{ name: 'Utilities', budgeted: 350, spent: 189, color: '#f97316', bg: 'rgba(249,115,22,0.1)' },
{ name: 'Savings', budgeted: 900, spent: 850, color: '#06b6d4', bg: 'rgba(6,182,212,0.1)' },
];

let savingsGoals = [
{ name: 'Emergency Fund', saved: 4200, target: 10000, color: '#22c55e' },
{ name: 'Vacation to Japan', saved: 3100, target: 5000, color: '#6c63ff' },
{ name: 'New Laptop', saved: 900, target: 2000, color: '#3b82f6' },
{ name: 'Car Down Payment', saved: 6000, target: 15000, color: '#f59e0b' },
];

let recurringPayments = [
    { name: 'Housing', amount: 5000, dayOfMonth: 10 },
    { name: 'Transport', amount: 300, dayOfMonth: 5 }
];
let currentFilter = "all";

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

// ===== AUTH =====
let currentUser = null;

function validateEmail(email) {
    if (!email.trim()) {
        return "Email is required";
    }

    if (!email.includes("@")) {
        return "Email must include '@' (example: name@gmail.com)";
    }

    const parts = email.split("@");

    if (parts.length !== 2) {
        return "Email must contain only one '@'";
    }

    const [username, domain] = parts;

    if (!username) {
        return "Missing username before '@'";
    }

    if (!domain) {
        return "Missing domain after '@'";
    }

    if (!domain.includes(".")) {
        return "Domain must include '.' (example: gmail.com)";
    }

    if (domain.startsWith(".")) {
        return "Domain can't start with '.'";
    }

    if (domain.endsWith(".")) {
        return "Domain can't end with '.'";
    }

    return null;
}

function switchTab(tab) {
document.querySelectorAll('.auth-tab').forEach((t, i) => {
t.classList.toggle('active', (i === 0 && tab === 'login') || (i === 1 && tab === 'signup'));
});
document.getElementById('login-form').style.display = tab === 'login' ? '' : 'none';
document.getElementById('signup-form').style.display = tab === 'signup' ? '' : 'none';
document.getElementById('auth-title').textContent = tab === 'login' ? 'Welcome back' : 'Create account';
document.getElementById('auth-sub').textContent = tab === 'login' ? 'Sign in to your account to continue' : 'Start managing your finances today';
}

function doLogin() {
    const email = document.getElementById('login-email').value;

    const error = validateEmail(email);

    if (error) {
        showToast(error, "error");
        return;
    }

    const name = email.split('@')[0]
        .replace(/\./g,' ')
        .replace(/\b\w/g, l => l.toUpperCase());

    showToast("Logged in successfully", "success");
    launchApp({ name, email });
}

function doSignup() {
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;

    if (!name.trim()) {
        showToast("Name is required", "error");
        return;
    }

    const error = validateEmail(email);

    if (error) {
        showToast(error, "error");
        return;
    }

    showToast("Account created successfully", "success");
    launchApp({ name, email });
}

function launchApp(user) {
currentUser = user;
document.getElementById('auth-screen').classList.add('hidden');
document.getElementById('app').style.display = 'flex';
document.getElementById('user-name-sidebar').textContent = user.name;
document.getElementById('user-email-sidebar').textContent = user.email;
document.getElementById('user-avatar').textContent = user.name.charAt(0).toUpperCase();
document.getElementById('greet-name').textContent = user.name.split(' ')[0];
initApp();
}

// Demo: auto-login for preview
window.addEventListener('load', () => {
// Uncomment to skip auth: launchApp({name:'Alex Johnson',email:'alex@email.com'});
});

// ===== NAVIGATION =====
function navigate(page) {
document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
document.getElementById(`page-${page}`).classList.add('active');
document.querySelectorAll('.nav-item').forEach(btn => {
if (btn.getAttribute('onclick')?.includes(page)) btn.classList.add('active');
});

// Init page-specific charts
setTimeout(() => {
if (page === 'reports') initReportCharts();
if (page === 'budget') initBudgetChart();
if (page === 'savings') initSavingsChart();
}, 50);
}

// ===== THEME =====
function toggleTheme() {
const html = document.documentElement;
const isDark = html.dataset.theme === 'dark';
html.dataset.theme = isDark ? 'light' : 'dark';
document.getElementById('theme-toggle').classList.toggle('on', !isDark);
setTimeout(() => refreshCharts(), 100);
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

function saveTransaction() {
  const name = document.getElementById("tx-name").value;
  const amount = Number(document.getElementById("tx-amount").value);
  const type = document.getElementById("tx-type").value;
  const category = document.getElementById("tx-category").value;

 if (!name.trim()) {
    showToast("Transaction name required", "error");
    return;
}

if (amount <= 0) {
    showToast("Amount must be greater than 0", "error");
    return;
}

if (!category) {
    showToast("Please select a category", "error");
    return;
}
  transactions.unshift({
    name,
    category,
    date: new Date().toLocaleDateString(),
    amount: type === "expense" ? -Math.abs(amount) : Math.abs(amount)
  });

  const cat = budgetCategories.find(c => c.name === category);
  if(cat && type === "expense"){
      cat.spent += Math.abs(amount);
  }

  closeTxModal();

  renderTransactions("all-transactions");
  renderTransactions("recent-tx", 6);
  renderBudgetOverview();
  renderBudgetCards();
  renderReportTable();
  checkBudgetLimits();
  initDashboardCharts();
  showToast("Transaction added successfully", "success")
}

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

function saveCategory() {
const name = document.getElementById("cat-name").value;
const budgeted = Number(document.getElementById("cat-budget").value);

if (!name.trim()) {
    showToast("Category name required", "error");
    return;
}

if (budgeted <= 0) {
    showToast("budgeted must be greater than 0", "error");
    return;
}

budgetCategories.push({
name,
budgeted,
spent: 0,
color: "#6c63ff"
});

closeCatModal();

renderBudgetOverview();
renderBudgetCards();
renderReportTable();
checkBudgetLimits();
showToast("Category saved successfully", "success")
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

function initDashboardCharts() {
const c = getColors();
const months = ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'];

// Income vs Expense bar chart
destroyChart('incomeExpenseChart');
chartInstances['incomeExpenseChart'] = new Chart(
document.getElementById('incomeExpenseChart'),
{
type: 'bar',
data: {
labels: months,
datasets: [
{
label: 'Income',
data: [6200, 6500, 6800, 7000, 7200, 7200],
backgroundColor: c.accent + '99',
borderColor: c.accent,
borderWidth: 2,
borderRadius: 8,
},
{
label: 'Expenses',
data: [4800, 5100, 4600, 4900, 4600, 4350],
backgroundColor: c.red + '66',
borderColor: c.red,
borderWidth: 2,
borderRadius: 8,
}
]
},
options: {
responsive: true, maintainAspectRatio: false,
plugins: { legend: { display: false } },
scales: {
x: { grid: { color: c.grid }, ticks: { color: c.text, font: { family: 'Sora', size: 11 } } },
y: { grid: { color: c.grid }, ticks: { color: c.text, font: { family: 'Sora', size: 11 }, callback: v => '$' + (v/1000).toFixed(0) + 'k' } }
}
}
}
);

// Donut chart
destroyChart('categoryDonutChart');
chartInstances['categoryDonutChart'] = new Chart(
document.getElementById('categoryDonutChart'),
{
type: 'doughnut',
data: {
labels: ['Food', 'Housing', 'Transport', 'Shopping', 'Health', 'Other'],
datasets: [{
data: [980, 1800, 280, 520, 190, 580],
backgroundColor: [c.orange, c.accent, c.blue, c.purple, c.green, '#94a3b8'],
borderWidth: 0,
hoverOffset: 8,
}]
},
options: {
responsive: true, maintainAspectRatio: false,
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

function initReportCharts() {
const c = getColors();
const months = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'];

destroyChart('trendChart');
chartInstances['trendChart'] = new Chart(document.getElementById('trendChart'), {
type: 'line',
data: {
labels: months,
datasets: [
{
label: 'Income',
data: [5800, 6200, 6500, 6800, 7000, 7200, 7200],
borderColor: c.green, backgroundColor: c.green + '20',
tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: c.green,
},
{
label: 'Expenses',
data: [4900, 4800, 5100, 4600, 4900, 4600, 4350],
borderColor: c.red, backgroundColor: c.red + '15',
tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: c.red,
},
{
label: 'Savings',
data: [900, 1400, 1400, 2200, 2100, 2600, 2850],
borderColor: c.accent, backgroundColor: c.accent + '15',
tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: c.accent,
}
]
},
options: {
responsive: true, maintainAspectRatio: false,
plugins: { legend: { display: false } },
scales: {
x: { grid: { color: c.grid }, ticks: { color: c.text, font: { family: 'Sora', size: 11 } } },
y: { grid: { color: c.grid }, ticks: { color: c.text, font: { family: 'Sora', size: 11 }, callback: v => '$' + v.toLocaleString() } }
}
}
});

destroyChart('reportPieChart');
chartInstances['reportPieChart'] = new Chart(document.getElementById('reportPieChart'), {
type: 'pie',
data: {
labels: budgetCategories.map(b => b.name),
datasets: [{
data: budgetCategories.map(b => b.spent),
backgroundColor: [c.orange, c.accent, c.blue, c.red, c.purple, c.green, '#f97316', '#06b6d4'],
borderWidth: 0,
}]
},
options: {
responsive: true, maintainAspectRatio: false,
plugins: {
legend: { position: 'right', labels: { color: c.text, font: { family: 'Sora', size: 11 }, boxWidth: 10, padding: 8 } }
}
}
});

destroyChart('weeklyChart');
chartInstances['weeklyChart'] = new Chart(document.getElementById('weeklyChart'), {
type: 'bar',
data: {
labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
datasets: [{
label: 'Spending',
data: [980, 1240, 1050, 1080],
backgroundColor: c.accent + 'cc',
borderColor: c.accent,
borderWidth: 0,
borderRadius: 10,
}]
},
options: {
responsive: true, maintainAspectRatio: false,
plugins: { legend: { display: false } },
scales: {
x: { grid: { display: false }, ticks: { color: c.text, font: { family: 'Sora', size: 11 } } },
y: { grid: { color: c.grid }, ticks: { color: c.text, font: { family: 'Sora', size: 11 }, callback: v => '$' + v } }
}
}
});
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
responsive: true, maintainAspectRatio: false,
plugins: {
legend: { labels: { color: c.text, font: { family: 'Sora', size: 12 }, boxWidth: 12 } }
},
scales: {
x: { grid: { display: false }, ticks: { color: c.text, font: { family: 'Sora', size: 11 } } },
y: { grid: { color: c.grid }, ticks: { color: c.text, font: { family: 'Sora', size: 11 }, callback: v => '$' + v } }
}
}
});
}

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
backgroundColor: [c.green, c.accent, c.blue, c.orange].map(x => x + '99'),
borderColor: [c.green, c.accent, c.blue, c.orange],
borderWidth: 2,
borderRadius: 8,
}
]
},
options: {
responsive: true, maintainAspectRatio: false,
plugins: {
legend: { labels: { color: c.text, font: { family: 'Sora', size: 12 }, boxWidth: 12 } }
},
scales: {
x: { grid: { display: false }, ticks: { color: c.text, font: { family: 'Sora', size: 10 } } },
y: { grid: { color: c.grid }, ticks: { color: c.text, callback: v => '$' + (v/1000).toFixed(0) + 'k' } }
}
}
});
}

function refreshCharts() {
const active = document.querySelector('.page.active')?.id?.replace('page-', '');
if (active === 'dashboard') initDashboardCharts();
if (active === 'reports') initReportCharts();
if (active === 'budget') initBudgetChart();
if (active === 'savings') initSavingsChart();
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
    const budgetDateElement = document.getElementById('current-budget-date');
    if (!displayElement) return;

    const now = new Date();
    const options = { month: 'long', year: 'numeric' };
    const dateString = now.toLocaleDateString('en-US', options);

    displayElement.textContent = `📅 ${dateString}`;
    if (budgetDateElement) budgetDateElement.textContent = dateString;
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
if (budgetDateElement) budgetDateElement.textContent = dateString;
}

Chart.defaults.font.family = 'Sora';