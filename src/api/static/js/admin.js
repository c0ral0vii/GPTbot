const API_TOKEN = localStorage.getItem('admin_token')
const API_BASE = '/api/v1'

async function fetchAPI(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'X-Admin-Token': API_TOKEN,
            ...options.headers,
        }
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`)
    }
    return response.json()
}


async function loadOverviewStats() {
    try {
        const stats = await fetchAPI('/stats/overview');
        document.getElementById('totalUsers').textContent = stats.total_users;

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadOverviewStats();

    setInterval(loadOverviewStats, 30000);
})


class AdminDashboard {
    constructor() {
        this.charts = new DashboardCharts();
        this.updateInterval = 30000;
        this.statsUpdateInterval = 50000;
    }

    async initialize() {
        await this.charts.initializeCharts();
        this.startUpdateCycles()
    }

    startUpdateCycles() {
        setInterval(() => this.updateAllData(), this.updateInterval);
    }

    async updateAllData() {
        try {
            await Promise.all([
                this.charts.updateCharts(),
            ]);
        } catch (error) {
            console.error("Error updating dashboard: ", error);
        }
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const dashboard = new AdminDashboard();
    await dashboard.initialize();
});


class AdminPanel {
    constructor() {
        this.charts = null;
        this.initializeEventListeners();
    }

    async initialize() {
        this.charts = new DashboardCharts();

        await this.loadDashboardData();

        setInterval(() => this.refreshData(), 30000);
    }

    initializeEventListeners() {
        document.getElementById('refreshButton').addEventListener('click', () => {
            this.refreshData();
        });

        document.querySelectorAll('[data-period]').forEach(button => {
            button.addEventListener('click', (e) => {
                const period = e.target.dataset.period;
                this.charts.updateActivityPeriod(period);
            });
        });
    }

    showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 end-0 m-3';
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }

    async loadDashboardData() {
        try {
            this.showLoader();

            const [overviewData] = await Promise.all([
                fetchAPI('/stats/overview')
            ]);
            this.updateOverviewStats(overviewData);

            this.updateLastUpdateTime();

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoader();
        }
    }

    updateLastUpdateTime() {
        const now = new Date();
        document.getElementById('lastUpdateTime').textContent = now.toLocaleTimeString();
    }

    showLoader() {
        document.getElementById('loader').classList.add('active');
    }

    hideLoader() {
        document.getElementById('loader').classList.remove('active');
    }

    updateOverviewStats(data) {
        document.getElementById('totalUsers').textContent = data.total_users;
        document.getElementById('activeToday').textContent = data.active_today;
        document.getElementById('activeSubscriptions').textContent = data.active_subscriptions;
        document.getElementById('totalRevenue').textContent = `$${data.total_revenue}`;

        const statusElement = document.getElementById('systemStatus');
        statusElement.textContent = data.system_status;
        statusElement.className = `status-${data.system_status.toLowerCase()}`;
    }

    async refreshData() {
        await this.loadDashboardData();
    }
}

let adminPanel;
document.addEventListener('DOMContentLoaded', async () => {
    adminPanel = new AdminPanel();
    await adminPanel.initialize();
});