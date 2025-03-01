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
//
// document.addEventListener('DOMContentLoaded', () => {
//     loadOverviewStats();
//
//     setInterval(loadOverviewStats, 30000);
// })


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
                loadOverviewStats(),
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
        this.currentUsersPage = 1;
        this.usersPerPage = 50;
        this.searchTerm = '';
        this.initializeEventListeners();
    }

    async initialize() {
        this.charts = new DashboardCharts();

        await this.loadDashboardData();

        // setInterval(() => this.refreshData(), 30000);
    }

    initializeEventListeners() {
         document.getElementById('groupSearch').addEventListener('input', (e) => {
            this.searchTerm = e.target.value;
            this.loadItems();
        });

        document.getElementById('refreshButton').addEventListener('click', () => {
            this.refreshData();
        });

        document.getElementById('premium_active').addEventListener('change', function() {
            const premiumDatesContainer = document.getElementById('premium_dates');
            if (this.checked) {
                premiumDatesContainer.style.display = 'block'; // Показываем поля
            } else {
                premiumDatesContainer.style.display = 'none'; // Скрываем поля
            }
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

            const [overviewData, userData] = await Promise.all([
                fetchAPI('/stats/overview'),
                fetchAPI('/users')
            ]);

            this.updateOverviewStats(overviewData);
            this.updateUserTable(userData)

            this.updateLastUpdateTime();

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoader();
        }
    }

    async saveChange(user_id) {
        let updatedData = {
            "user_id": document.getElementById('user_id').value,
            "energy": document.getElementById('energy').value,
            "referral_link": document.getElementById('referral_link').value,
            "use_referral_link": document.getElementById('use_referral_link').value,
            "premium_active": document.getElementById('premium_active').checked, // Чекбокс, используем .checked
            "banned_user": document.getElementById('banned_user').checked, // Чекбокс, используем .checked
            "created": document.getElementById('created').value,
            "last_used": document.getElementById('last_used').value,
        };
        console.log(updatedData);
        const response = await this.fetchAPI(`/users/${user_id}/change`, {
            "method": "PUT",
            "body": JSON.stringify(updatedData)
        });

        if (response.ok) {
            await this.showToast("Изменения успешно сохранены");
        } else {
            await this.showError("Ошибка при сохранении изменений");
        }
        await this.loadDashboardData();
    }

    async getMoreInfo(user_id) {
        const data = await this.fetchAPI(`/users/${user_id}/info`);

        document.getElementById('user_id').value = data.user_id;
        document.getElementById('energy').value = data.energy;
        document.getElementById('referral_link').value = data.referral_link;
        document.getElementById('use_referral_link').value = data.use_referral_link;

        // Обновляем чекбокс премиума
        const premiumCheckbox = document.getElementById('premium_active');
        const premiumDatesContainer = document.getElementById('premium_dates');

        premiumCheckbox.checked = data.status;
        premiumDatesContainer.style.display = data.status ? 'block' : 'none';

        document.getElementById('banned_user').checked = data.banned_user;
        document.getElementById('created').value = data.created;
        document.getElementById('last_used').value = data.last_used;

        const modal = new bootstrap.Modal(document.getElementById('editModal'));
        document.getElementById("saveItemButton").onclick = () => {
            adminPanel.saveChange(user_id);
        };

        modal.show();
        await this.loadDashboardData();
    }


    async bannedUser(user_id) {
        await this.fetchAPI(`/users/${user_id}/banned`)

        await this.showToast("Пользователь заблокирован")
        await this.loadDashboardData()
    }

    updateUserTable(data) {
        const tbody = document.querySelector('#groupsTable tbody');
        tbody.innerHTML = '';

        data.items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.id}</td>
                <td>${item.user_id}</td>
                <td>${item.status}</td>
                <td>${item.energy}</td>
                <td>${item.created}</td>
                <td>${item.updated}</td>
                   
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary"
                            onclick="adminPanel.getMoreInfo(${item.id})">
                            Изменить
                        </button>
                        <button class="btn btn-sm btn-danger"
                            onclick="adminPanel.bannedUser(${item.id})">
                            Заблокировать
                        </button>
                    </div>
                </td>
                
            `;
            tbody.appendChild(row);
        });

        this.updatePagination(data.total, data.page, data.total_pages);
    }

    updatePagination(total, currentPage, totalPages) {
        const pagination = document.getElementById('groupsPagination');
        pagination.innerHTML = '';

        document.getElementById('showingCount').textContent = Math.min(this.usersPerPage, total);
        document.getElementById('totalCount').textContent = total;

        if (totalPages > 1) {
            const pages = [];

            pages.push(1);

            for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
                pages.push(i);
            }

            if (totalPages > 1) {
                pages.push(totalPages);
            }

            pages.forEach((page, index) => {
                if (index > 0 && pages[index] - pages[index - 1] > 1) {
                    pagination.appendChild(this.createPaginationItem('...', false));
                }
                pagination.appendChild(this.createPaginationItem(page, page === currentPage));
            });
        }
    }

    createPaginationItem(text, isActive) {
        const li = document.createElement('li');
        li.className = `page-item${isActive ? ' active' : ''}`;

        const a = document.createElement('a');
        a.className = 'page-link';
        a.href = '#';
        a.textContent = text;

        if (text !== '...') {
            a.onclick = (e) => {
                e.preventDefault();
                this.currentUsersPage = parseInt(text);
                this.loadItems();
            };
        }

        li.appendChild(a);
        return li;
    }

    async fetchAPI(endpoint, options = {}) {
        const response = await fetch(`/api/v1${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        return response.json();
    }

    async loadItems() {
            try {
                const params = new URLSearchParams({
                    skip: (this.currentUsersPage - 1) * this.usersPerPage,
                    limit: this.usersPerPage,
                    search: this.searchTerm,
                });

                const groupsData = await this.fetchAPI(`/users?${params}`);
                this.updateUserTable(groupsData);

            } catch (error) {
                console.error('Error loading items:', error);
                this.showError('Failed to load items');
            }
        }

    updateLastUpdateTime() {
        const now = new Date();
        document.getElementById('lastUpdateTime').textContent = now.toLocaleTimeString();
    }

    async showToast(message) {
        const toastContainer = document.getElementById('toastContainer');

        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-bg-success border-0 position-relative';
        toast.role = 'alert';
        toast.ariaLive = 'assertive';
        toast.ariaAtomic = 'true';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        const bootstrapToast = new bootstrap.Toast(toast, {
            delay: 2000
        });
        bootstrapToast.show();

        // Optional: Remove the toast after it’s hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
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
        document.getElementById('totalRevenue').textContent = `${data.total_revenue}₽`;

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