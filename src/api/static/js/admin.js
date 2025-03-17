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

        // document.getElementById('premium_active').addEventListener('change', function () {
        //     const premiumDatesContainer = document.getElementById('premium_dates');
        //     premiumDatesContainer.style.display = this.checked ? 'block' : 'none';
        // });


        document.getElementById('premium_active').addEventListener('change', function () {
            document.getElementById('premium_dates').style.display = this.checked ? 'block' : 'none';
        });

        document.getElementById('addAssistantButton').addEventListener('click', () => {
            this.openAddAssistantModal();
        });

        // Обработчик для кнопки "Сохранить" в модальном окне добавления
        document.getElementById('saveAssistantButton').addEventListener('click', () => {
            this.addAssistant();
        });

        // Обработчик для кнопки "Сохранить изменения" в модальном окне редактирования
        document.getElementById('saveEditAssistantButton').addEventListener('click', () => {
            const assistantId = document.getElementById('editAssistantId').value;
            this.saveAssistantChanges(assistantId);
        });
        document.getElementById('addAssistantModal').addEventListener('hidden.bs.modal', () => {
            this.clearAssistantModal(); // Очищаем поля
        });
    }

    async openAddAssistantModal() {
        const modal = new bootstrap.Modal(document.getElementById('addAssistantModal'));
        modal.show();
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

            const [overviewData, userData, assistData] = await Promise.all([
                fetchAPI('/stats/overview'),
                fetchAPI('/users'),
                fetchAPI('/assistants')
            ]);

            this.updateOverviewStats(overviewData);
            this.updateUserTable(userData);
            this.updateAssisTable(assistData);

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
            "use_referral_link": document.getElementById('use_referral_link').value,
            "premium_active": document.getElementById('premium_active').checked,
            "banned_user": document.getElementById('banned_user').checked,
            "personal_percent": document.getElementById('personal_percent').value,
            "referral_bonus": document.getElementById('referral_bonus').value,
            "auto_renewal": document.getElementById('auto_renewal').checked,
        };

        // Добавляем premium_dates, если премиум включен
        if (updatedData.premium_active) {
            updatedData.premium_dates = {
                "from": document.getElementById("premium_from").value,
                "to": document.getElementById("premium_to").value
            };
        }

        console.log(updatedData);

        const response = await this.fetchAPI(`/users/${user_id}/change`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(updatedData)
        });

        console.log(response);

        if (response.success) {
            await this.showToast("✅ Изменения успешно сохранены!");
        } else {
            await this.showError("❌ Ошибка при сохранении изменений!");
        }

        await this.loadDashboardData();
    }

    clearAssistantModal() {
        document.getElementById('assistantName').value = '';
        document.getElementById('assistantId').value = '';
        document.getElementById('assistantEnergyCost').value = '';
        document.getElementById('assistantComment').value = '';
        document.getElementById('assistantPremiumFree').checked = false;
        document.getElementById('assistantEnabled').checked = false;
    }
    async addAssistant() {
        const newAssistant = {
            title: document.getElementById('assistantName').value,
            assistant_id: document.getElementById('assistantId').value,
            energy_cost: parseFloat(document.getElementById('assistantEnergyCost').value),
            comment: document.getElementById('assistantComment').value,
            premium_free: document.getElementById('assistantPremiumFree').checked,
            disable: document.getElementById('assistantEnabled').checked,
        };

        try {
            const response = await this.fetchAPI('/assistants/create', {
                method: 'POST',
                body: JSON.stringify(newAssistant),
            });
            const modal = bootstrap.Modal.getInstance(document.getElementById('addAssistantModal'));
            modal.hide();

            if (response.success) {
                await this.showToast('✅ Ассистент успешно добавлен!');
            } else {
                await this.showError('❌ Ошибка при добавлении ассистента!');
            }
            await this.loadDashboardData();

        } catch (error) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addAssistantModal'));
            modal.hide();
            console.error('Error adding assistant:', error);
            await this.showError('❌ Ошибка при добавлении ассистента!');
        }
    }

    async getMoreInfo(user_id) {
        const data = await this.fetchAPI(`/users/${user_id}/info`);
        console.log(data);

        document.getElementById('user_id').value = data.user_id;
        document.getElementById('energy').value = data.energy;
        document.getElementById('use_referral_link').value = data.use_referral_link;

        document.getElementById('personal_percent').value = data.personal_percent;
        document.getElementById('referral_bonus').value = data.referral_bonus;

        const auto_renewal = document.getElementById('auto_renewal');
        auto_renewal.checked = data.auto_renewal;

        const premiumCheckbox = document.getElementById('premium_active');
        const premiumDatesContainer = document.getElementById('premium_dates');

        premiumCheckbox.checked = data.premium_active;
        premiumDatesContainer.style.display = data.premium_active ? 'block' : 'none';

        if (data.premium_dates) {
            document.getElementById('premium_from').value = data.premium_dates.from;
            document.getElementById('premium_to').value = data.premium_dates.to;
        } else {
            document.getElementById('premium_from').value = "";
            document.getElementById('premium_to').value = "";
        }

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

    async getAssistantInfo(assistant_id) {
        const data = await this.fetchAPI(`/assistants/${assistant_id}/info`);

        // Заполняем поля модального окна
        document.getElementById('editAssistantName').value = data.title;
        document.getElementById('editAssistantId').value = data.assistant_id;
        document.getElementById('editAssistantEnergyCost').value = data.energy_cost;
        document.getElementById('editAssistantComment').value = data.comment;
        document.getElementById('editAssistantPremiumFree').checked = data.premium_free;
        document.getElementById('editAssistantEnabled').checked = data.disable;

        // Открываем модальное окно
        const modal = new bootstrap.Modal(document.getElementById('editAssistantModal'));
        modal.show();

        // Назначаем обработчик для кнопки "Сохранить изменения"
        document.getElementById('saveEditAssistantButton').onclick = () => {
            this.saveAssistantChanges(assistant_id);
        };
    }

    async saveAssistantChanges(assistant_id) {
        const updatedData = {
            title: document.getElementById('editAssistantName').value,
            assistant_id: document.getElementById('editAssistantId').value,
            energy_cost: parseFloat(document.getElementById('editAssistantEnergyCost').value),
            comment: document.getElementById('editAssistantComment').value,
            premium_free: document.getElementById('editAssistantPremiumFree').checked,
            disable: document.getElementById('editAssistantEnabled').checked,
        };

        const response = await this.fetchAPI(`/assistants/${assistant_id}/change`, {
            method: 'PUT',
            body: JSON.stringify(updatedData),
        });

        await this.showToast('✅ Изменения успешно сохранены!');
        await this.loadDashboardData();
        bootstrap.Modal.getInstance(document.getElementById('editAssistantModal')).hide();
    }

    updateAssisTable(data) {
        const tbody = document.querySelector('#assistantsTable tbody');
        tbody.innerHTML = '';

        data.items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.id}</td>
                <td>${item.title}</td>
                <td>${item.energy_cost}</td>
                <td>${item.status}</td>
                <td>${item.free_for_premium}</td>
                   
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary"
                            onclick="adminPanel.getAssistantInfo(${item.id})">
                            Изменить
                        </button>
                        
                    </div>
                </td>
                
            `;
            tbody.appendChild(row);
        });
    }

    updateUserTable(data) {
        const tbody = document.querySelector('#groupsTable tbody');
        tbody.innerHTML = '';

        data.items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.id}</td>
                <td>${item.user_id}</td>
                <td>${item.status }</td>
                <td>${item.energy}</td>
                <td>${item.created}</td>
                <td>${item.updated}</td>
                   
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary"
                            onclick="adminPanel.getMoreInfo(${item.id})">
                            Изменить
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