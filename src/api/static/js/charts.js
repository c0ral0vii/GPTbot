class DashboardCharts {
    constructor() {
        this.charts = {};
        this.currentPeriod = '24h';
    }

    async initializeCharts() {
        await this.createActivityChart();
        await this.createUsersChart();
    }


    async createActivityChart() {
        const ctx = document.getElementById('activityChart').getContext("2d")
        const data = await this.fetchActivityData();

        this.charts.activity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Активность пользователя',
                    data: data.values,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: true
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    async createUsersChart() {
        const ctx = document.getElementById('usersChart').getContext('2d');
        const data = await this.fetchUsersData()

        this.charts.users = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Обычные пользователи', 'Пользователи с подпиской'],
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        'rgb(75, 192, 192)',
                        'rgb(255, 205, 86)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    async fetchActivityData() {
        try {
            const response = await fetch("/api/v1/analytics/activity");
            return await response.json()
        } catch (error) {
            console.error('Error fetching activity data:', error);
            return { labels: [], values: [] };
        }
    }

    async fetchUsersData() {
        try {
            const response = await fetch("/api/v1/users")
            return response.json()
        } catch (error) {
            console.error('Error fetching users data:', error);
            return { labels: [], values: [] };
        }
    }

    async updateCharts() {
        const activityData = await this.fetchActivityData();
        const usersData = await this.fetchUsersData();

        if (this.charts.activity) {
            this.charts.activity.data.labels = activityData.labels;
            this.charts.activity.data.datasets[0].data = activityData.values;
            this.charts.activity.update();
        }

        if (this.charts.users) {
            this.charts.users.data.datasets[0].data = usersData.values;
            this.charts.users.update();
        }
    }

    async updateActivityPeriod(period) {
        this.currentPeriod = period;
        await this.updateCharts();
    }

}